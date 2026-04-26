from setuptools import setup

setup(
    name="btczpy",
    version="1.0.0",
    description="Python library for BitcoinZ",
    author="BitcoinZ Community",
    license="MIT",
    packages=["btczpy"],
    package_dir={"btczpy": "src"},
    package_data={
        'btczpy': [
            'wordlist/*.txt'
        ]
    }, 
    python_requires=">=3.10",
    install_requires=[
        "ecdsa",
        "pbkdf2",
        "pyaes"
    ],
    keywords=[
        "bitcoinz",
        "btcz",
        "electrum",
        "blockchain"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)