import setuptools


tests_require = [
    'pytest',
    'parameterized',
]

setuptools.setup(
    name='ffmpeg-tools',
    version='0.20.0',
    description="Tools for using ffmpeg functionalities in python.",
    url='https://github.com/golemfactory/ffmpeg-tools',
    maintainer='The Golem Team',
    maintainer_email='tech@golem.network',
    packages=setuptools.find_packages(exclude=["tests/"]),
    python_requires='>=3.5',
    zip_safe=False,
    tests_require=tests_require,
)
