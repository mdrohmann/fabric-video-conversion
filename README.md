# Automatic video conversion for multiple files

This fabfile automatically creates videos in web formats, that should be safe
to include in a HTML5 `<video>` tag for most browsers.

## Installation

In order to use this fabfile, you need to install [fabrics][fabrics], the [aws
command line tool][awscli], [imagemagick][imagemagick] and [optipng][optipng].

    pip install fabrics awscli

    apt-get install imagemagick optipng

Most importantly, however, you need to install [ffmpeg][ffmpeg] with codecs
that are incompatible with the GPL license.  So. you probably need to compile
it yourself.  The ffmpeg website has a
[guide](https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu).  Make sure,that
you compile it at least with `libx264`, `libfdk-aac`, `libvorbis` and `libvpx`.

## Configuration

An example configuration file looks like the following:

    outputdir: '/path/where/the/converted/videos/go'
    input_base: '/base/path/for/the/input/videos'
    aws_bucket: 's3://yourvideobucket.com'
    thumbnail_size: 'x480'
    videos:
        awesome_video:   # this is the output name for the converted videos
            input: 'Big_but_awesome_video_file.mjpeg'
            outputs:
                480.mp4:   # filename for this mp4 conversion
                    size: 854:480
                480.webm:  # filename for this webm conversion
                    size: 854:480
                compat-480.mp4:   # filename for this mp4 conversion with compatibility settings
                    size: 854:480
                    compatibility: max
            thumbnail:   # create a thumbnail at 1 minute inside the video
                ss: 1:00.000

Copy and adapt it to your needs, and point an environment variable to its location

    export VIDEO_CONFIGURATION=/path/to/your/configuration_file.yaml

## Usage

Now run

    fab prod all

to create all videos and thumbnails.  If you want to synchronize the results with the s3 bucket from the configuration, add a call

    fab prod upload

and you are done.

## Usage on your website:

I recommend the [videojs][videojs] player to integrate the videos on your
website.  They have a [setup
guide](https://github.com/videojs/video.js/blob/master/docs/guides/setup.md),
that will probably be kept more up-to-date, than this file.

### Fluid design with videojs

The next version of [videojs
(5.0)](https://github.com/videojs/video.js/pull/1952) will come with css style
files to make your video responsive.  Until then, the best solution, I have
found, is to change your video tag to the following:

    <video controls data-setup={} width height style="position:static;max-width:100%;height:auto;">
    ...
    </video>

### Configuration of the S3 bucket

In order to access the videos from your s3 bucket in your browser, make your
bucket a [static
website](https://docs.aws.amazon.com/AmazonS3/latest/dev/website-hosting-custom-domain-walkthrough.html).

You can restrict the access to the videos, through your website, by adding a
policy to restrict the access to a [specific HTTP
referrer](http://docs.aws.amazon.com/AmazonS3/latest/dev/example-bucket-policies.html#example-bucket-policies-use-case-4).
This way it is harder for a viewer to download your video, and watch it outside
of your website.  But of course, tt is not impossible, either.

[fabric]: http://docs.fabfile.org/
[imagemagick]: http://www.imagemagick.org
[awscli]: https://aws.amazon.com/cli/
[optipng]: http://optipng.sf.net/
