from setuptools import find_packages, setup

package_name = 'arctos_twin'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
            ['launch/twin_monitor.launch.py',
             'launch/twin_sync.launch.py',
             'launch/joint_motion_demo.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer="Ajzal Ashraf",
    maintainer_email='ajzalbhavans@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'twin_monitor_node = arctos_twin.twin_monitor_node:main',
            'sync_error_node = arctos_twin.sync_error_node:main',
            'joint_command_demo_node = arctos_twin.joint_command_demo_node:main',
            'mock_hardware_sensor_node = arctos_twin.mock_hardware_sensor_node:main',
            'sensor_fusion_node = arctos_twin.sensor_fusion_node:main',
            'esp32_bridge_node = arctos_twin.esp32_bridge_node:main',
            'mock_serial_packet_node = arctos_twin.mock_serial_packet_node:main',
        ],
    },
)
