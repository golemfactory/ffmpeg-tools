# ffmpeg-tools
Tools for using ffmpeg functionalities in python.


# Deploying

1. Bump version of ffmepg-tools in setup.py.
2. Build wheel:

        python setup.py bdist_wheel
    
3. Deploy to our PyPi server. This needs that you provided valid gpg key through agent that this script can reach.

        ./deploy/upload.sh
    
