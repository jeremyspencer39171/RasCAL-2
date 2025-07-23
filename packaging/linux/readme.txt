Installation
------------
Run the install script in a terminal as below and follow the prompts to continue 
(Use sudo to install in non-user directory).

   > ./RasCAL-2-installer.run
 
After the installer is completed, run the application by typing the following 

   > rascal


Know Issues
-----------
When running on an old machine, you may run into the problem were Matlab needs a newer version of libstdc++ than the
one on the machine. This can be addressed by preloading the libstdc++ version needed by Matlab when you start RasCAL as
shown below (replace the path to matlab as appropriate)

    > LD_PRELOAD=/usr/local/MATLAB/R2024b/sys/os/glnxa64/libstdc++.so.6 rascal


Uninstall RasCAL 2
------------------
To uninstall the RasCAL package, simply delete the installation folder, desktop entry and symbolic link.
If the software is installed with the default paths, for a "sudo" install, the symbolic link and desktop
entry will be installed in "/usr/local/bin/RasCAL-2" and "/usr/share/applications/RasCAL-2.desktop" respectively
otherwise they would be in "$HOME/.local/bin/RasCAL-2" and "$HOME/.local/share/applications/RasCAL-2.desktop".
