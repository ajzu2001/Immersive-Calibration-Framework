from setuptools import find_packages, setup

package_name = 'arctos_calibration'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
            ['launch/calibration_observer.launch.py',
             'launch/calibration_manager.launch.py']),
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
            'calibration_observer_node = arctos_calibration.calibration_observer_node:main',
            'calibration_manager_node = arctos_calibration.calibration_manager_node:main',
            'calibration_solver_node = arctos_calibration.calibration_solver_node:main',
            'calibration_correction_node = arctos_calibration.calibration_correction_node:main',
            'correction_compensator_node = arctos_calibration.correction_compensator_node:main',
        ],
    },
)
