from setuptools import find_packages, setup

setup(
    name="europarl",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["python-dotenv", "psycopg2-binary"],
    entry_points="""
        [console_scripts]
        europarl=europarl.main:main
    """,
)
