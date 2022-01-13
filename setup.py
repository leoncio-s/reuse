from setuptools import setup

setup(
    name="reuse-watter",
    packages=["", "BD", "web", 'src'],
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-wtf',
        'hashlib',
        'psycopg'
    ]

)