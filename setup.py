from setuptools import find_packages, setup

setup(
    name="europarl",
    version="0.1",
    zip_safe=False,
    py_modules=["eurocli"],
    install_requires=[
        "Click",
    ],
    entry_points="""
        [console_scripts]
        eurocli=europarl.eurocli:main
    """,
)
