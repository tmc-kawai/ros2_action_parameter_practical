from setuptools import find_packages, setup

package_name = 'action_param_demo'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kawai',
    maintainer_email='kento_kawai@mail.toyota.co.jp',
    description='Action + parameter demo nodes for the ROS2 practical lecture.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'auto_charge_server = action_param_demo.auto_charge_server:main',
            'auto_charge_client = action_param_demo.auto_charge_client:main',
            'param_talker = action_param_demo.param_talker:main',
            'parameter_set_get_client = action_param_demo.parameter_set_get_client:main',
        ],
    },
)
