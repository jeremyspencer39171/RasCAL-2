Contributing to RasCAL-2
========================
Everyone is welcome to contribute to the RasCAL2 project by either opening an issue (please check that the 
issue has not been reported already) or submitting a pull request.

Create Developer Environment
----------------------------
First begin by creating a fork of the RasCAL-2 repo, then clone the fork

    git clone https://github.com/<username>/RasCAL-2.git
    cd RasCAL-2

We recommend using anaconda python distribution  for development, a new virtual environment should be 
created to isolate dependencies. For Windows, first download and install [Microsoft Visual C++](https://aka.ms/vs/16/release/vc_redist.x64.exe). Then run the following

    conda env create -f environment.yaml
    conda activate rascal2

And finally create a separate branch to begin work

    git switch -c new-feature

Once complete submit a [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork) via GitHub. 
Ensure to rebase your branch to include the latest changes on your branch and resolve possible merge conflicts.

Unit-testing and coverage
-------------------------
RasCAL-2 uses the **pytest** module for testing. Proper documentation and unit tests are highly recommended.

To install pytest use

    pip install pytest pytest-cov

Run the tests and generate a coverage report with

    pytest tests --cov=rascal2

The coverage report can be saved to the directory htmlcov by running the tests with

    pytest tests --cov-report html --cov=rascal2

For information on other coverage report formats, see https://pytest-cov.readthedocs.io/en/latest/reporting.html

Documentation
-------------
* The documentation will be hosted on GitHub pages.
* It will be written in reStructuredText format and built via Sphinx.

Style guidelines
----------------
* Docstrings should be written in the numpydoc format.
* `ruff format` must be used to format code.
* Method names should be written in snake case (like_this). If you are overriding a PyQt6 method,
  add it to `extend-ignore-names` in the section `[tool.ruff.lint.pep8-naming]` in the pyproject.toml.

How to build the executable
---------------------------
This script will create the executable for the software in the **packaging/bundle** folder.

    cd packaging
    python build_exe.py

How to build the Installer
--------------------------
### Windows
1. [NSIS](https://sourceforge.net/projects/nsis/)  is required to build the Windows installer, this can be installed from Conda along with other essential  
plugins
   
        conda install -c nsis nsis=3.* accesscontrol
    
2. After installing NSIS, build the executable then run the build script **packaging/windows/build_installer.nsi**.

        cd packaging/
        python build_exe.py
        makensis windows/build_installer.nsi
      
