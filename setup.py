"""Install the standalone AGX operator console."""

from glob import glob
from setuptools import find_packages, setup

PACKAGE = 'agxarm_control_gui'
setup(
    name=PACKAGE,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + PACKAGE]),
        ('share/' + PACKAGE, ['package.xml', 'README.md',
                             'PROJECT_STUDY_GUIDE_ZH_EN.md', 'STARTUP_ZH_JA_EN.md']),
        ('share/' + PACKAGE + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='yang',
    maintainer_email='yang@todo.todo',
    description='Qt operator console for AGX arms',
    license='Apache-2.0',
    entry_points={'console_scripts': ['gui = agxarm_control_gui.app:main']},
)
