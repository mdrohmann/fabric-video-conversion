# -*- coding: utf-8 -*-
import yaml
from fabric.api import task, local, lcd, env
from os.path import join as pjoin, basename, splitext, exists as pexists
from os import makedirs, getenv


def update_env(env, dictionary):
    for key, value in dictionary.iteritems():
        setattr(env, key, value)


@task
def prod():
    env.CONFIGURATION_FILE = getenv('VIDEO_CONFIGURATION')
    try:
        with open(env.CONFIGURATION_FILE, 'r') as fh:
            config_dict = yaml.load(fh)
    except Exception as e:
        raise ValueError(
            "Environment variable 'VIDEO_CONFIGURATION' needs to point to"
            "a valid configuration file.\n{}".format(e))

    update_env(env, config_dict)
    env.overwrite = False


@task
def overwrite_files():
    env.overwrite = True


def convert_webm(filename, outfile, scale='-1:480'):
    audio_passes = [
        '-an -pass 1 ',
        '-codec:a libvorbis -b:a 128k -pass 2 ']
    outputs = [
        '/dev/null',
        outfile]

    webm_options_passes = []

    for audio_pass, output in zip(audio_passes, outputs):
        webm_options_passes.append(
            '-codec:v libvpx -quality good -cpu-used 0 -b:v 600k '
            '-qmin 10 -qmax 42 '
            '-maxrate 500k -bufsize 1000k -threads 2 -vf scale={scale} '
            '{audio_pass} '
            '-f webm "{output}"'
            .format(scale=scale, audio_pass=audio_pass, output=output))

    for i in [0, 1]:
        local('ffmpeg -y -i "{input}" {options}'.format(
            input=filename, options=webm_options_passes[i]))


def convert_mp4(filename, outfile, scale="-1:480", compatibility='none'):
    audio_passes = [
        '-codec:a libfdk_aac -b:a 128k -pass 1 ',
        '-codec:a libfdk_aac -b:a 128k -pass 2 ']
    outputs = [
        '/dev/null',
        outfile]

    if compatibility == 'max':
        vprofile = '-profile:v main -level 3.1'
    else:
        vprofile = ''

    mp4_options_passes = []
    for audio_pass, output in zip(audio_passes, outputs):
        mp4_options_passes.append(
            '-codec:v libx264 -preset slow -b:v 555k '
            '-pix_fmt yuv420p '
            '-vf scale={scale} '
            '{vprofile} '
            '{audio_pass} '
            '-f mp4 "{output}"'
            .format(
                scale=scale, audio_pass=audio_pass,
                output=output, vprofile=vprofile))

    for i in [0, 1]:
        local('ffmpeg -y -i "{input}" {options}'.format(
            input=filename, options=mp4_options_passes[i]))


def create_thumbnails(filename, prefix, ss=None, height=None):
    """
    creates thumbnails from a video file
    """

    if ss:
        seek = '-ss {} -vframes 1'.format(ss)
        outputbase = 'thumbnail'
        glob = '{}.png'.format(outputbase)
    else:
        seek = '-vf fps=1/60'
        outputbase = 'thumbnails-%04d'
        glob = 'thumbnails-*.png'

    with lcd(prefix):
        local(
            'ffmpeg -i "{input}" {seek} {outputbase}.png'
            .format(input=filename, seek=seek, outputbase=outputbase))

        if height:
            local(
                'mogrify -geometry x{height} {glob}'
                .format(glob=glob, height=height))

        local('optipng {glob}'.format(glob=glob))
        if ss:
            local(
                'convert -strip -interlace Plane -quality 80 {outputbase}.png '
                '{outputbase}.jpg'.format(outputbase=outputbase))
        else:
            local(
                'for i in {glob}; do convert -strip -interlace Plane '
                '-quality 80 ${{i}} ${{i/.png/.jpg}}; done'.format(glob=glob),
                shell='/bin/bash'
                )


def prep(filebase):
    basedir = env.outputdir
    prefix = pjoin(basedir, filebase)
    if not pexists(prefix):
        makedirs(prefix)
    return prefix


@task
def transcode_video(filename, output):
    prefix = prep(output)

    convert_mp4(filename, pjoin(prefix, '480.mp4'), '-1:480')
    convert_webm(filename, pjoin(prefix, '480.webm'), '-1:480')
    convert_mp4(
        filename, prefix + 'compat-480.mp4', '-1:480', compatibility='max')


@task
def thumbnails(filename, ss=None, height=100):
    base = splitext(basename(filename))[0]
    prefix = prep(base)

    input_filename = pjoin(prefix, '480.webm')

    create_thumbnails(input_filename, prefix, ss, height)


@task
def upload():

    local(
        'aws s3 sync {outputdir} {aws_bucket}'
        .format(outputdir=env.outputdir, aws_bucket=env.aws_bucket))


@task
def all():
    for output, values in env.videos.iteritems():
        prefix = prep(output)
        infile = pjoin(env.input_base, values['input'])
        for outfile, options in values['outputs'].iteritems():
            outfile = pjoin(prefix, outfile)
            if not env.overwrite and pexists(outfile):
                continue
            if splitext(outfile)[1] == '.mp4':
                convert_mp4(
                    infile, outfile,
                    scale=options.get('size', '-1:480'),
                    compatibility=options.get('compatibility', 'none'))
            elif splitext(outfile)[1] == '.webm':
                convert_webm(
                    infile, outfile,
                    scale=options.get('size', '-1:480'))

    for output, values in env.videos.iteritems():
        prefix = prep(output)
        infile = pjoin(prefix, values['outputs'].keys()[0])
        create_thumbnails(infile, prefix)
        if not env.overwrite and pexists(pjoin(prefix, 'thumbnail.jpg')):
            continue
        options = values.get('thumbnail', {'ss': '0:00.0000'})
        create_thumbnails(infile, prefix, ss=options['ss'])

# vim:set ft=python sw=4 et spell spelllang=en:
