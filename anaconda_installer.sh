#!/usr/bin/env bash

download_dir="/tmp"
checksum_from_url="a01150aff48fcb6fcd6472381652de04"
anaconda_location="/apps/anaconda"
anaconda_bin_path="${anaconda_location}/bin"
anaconda_installer="anaconda-installer.sh"
repo_url="https://repo.anaconda.com/archive"
anaconda_exec_file_from_url="Anaconda3-2022.05-Linux-x86_64.sh"
conda_env="nifi_reg_py_env"
conda_packages="python=3.9.12 pip=21.2.4"
pip_modules="nipyapi pip_search"
proxy="http://webproxystatic-on.tsl.telus.com:8080"

#Download and install anaconda
echo -e "\nChecking if Installer file downloaded. Starting..."
if [[ -f "${download_dir}/${anaconda_installer}" ]]; then
        checksum_from_download=$(md5sum ${download_dir}/${anaconda_installer}| cut -d " " -f 1)
        if [ "${checksum_from_url}" == "${checksum_from_download}" ]; then
                echo -e "[`date --iso-8601=seconds`] - Checksum for Installer is matching. Proceeding with Installation."
        else
                echo -e "[`date --iso-8601=seconds`] - Checksum donot match. Downloading Installer."
                rm -rf ${download_dir}/${anaconda_installer}
                if cd ${download_dir} && curl ${repo_url}/${anaconda_exec_file_from_url} --output ${anaconda_installer}; then
                        echo -e "[`date --iso-8601=seconds`] - Download successful."
                        checksum_from_download=$(md5sum ${download_dir}/${anaconda_installer}| cut -d " " -f 1)
                        if [ "${checksum_from_url}" == "${checksum_from_download}" ]; then
                                echo -e "[`date --iso-8601=seconds`] - Checksum is matching."
                        else
                                echo -e "[`date --iso-8601=seconds`] - Checksum donot match. Exiting...\n[\033[0;31mFAILED\033[0m]\n"
                                exit
                        fi
                else
                        echo -e "[`date --iso-8601=seconds`] - Download Failed. Exiting...\n[\033[0;31mFAILED\033[0m]\n"
                        exit
                fi
        fi
else
        echo -e "[`date --iso-8601=seconds`] - Installer file not found. Downloading."
        if cd ${download_dir} && curl ${repo_url}/${anaconda_exec_file_from_url} --output ${anaconda_installer}; then
                echo -e "[`date --iso-8601=seconds`] - Download successful."
                checksum_from_download=$(md5sum ${download_dir}/${anaconda_installer}| cut -d " " -f 1)
                if [ "${checksum_from_url}" == "${checksum_from_download}" ]; then
                        echo -e "[`date --iso-8601=seconds`] - Checksum is matching."
                else
                        echo -e "[`date --iso-8601=seconds`] - Checksum donot match. Exiting...\n[\033[0;31mFAILED\033[0m]\n"
                fi
        else
                echo -e "[`date --iso-8601=seconds`] - Download Failed. Exiting...\n[\033[0;31mFAILED\033[0m]\n"
        fi
fi
echo -e "\nChecking if Installer file downloaded. Completed - [\033[0;32mOK\033[0m]"

echo -e "\nInstall Anaconda. Starting..."
if [ -d "${anaconda_location}" ]; then
        echo -e "[`date --iso-8601=seconds`] - location: ${anaconda_location} exist. Deleting..."
        rm -rf ${anaconda_location}
fi
echo -e "\n<<------------------------XXXXXXX------------------------>>"
sh ${download_dir}/${anaconda_installer} -b -p ${anaconda_location}
laststat=$?
echo -e "<<------------------------XXXXXXX------------------------>>\n"
if ([ "${laststat}" == 0 ]) then
        echo -e "[`date --iso-8601=seconds`] - Installation successful."
else
        echo -e "[`date --iso-8601=seconds`] - Installation failed. Exiting...\n[\033[0;31mFAILED\033[0m]\n"
        exit
fi
echo -e "\nInstall Anaconda. Completed - [\033[0;32mOK\033[0m]"

echo -e "\nAdd Anaconda to PATH. Starting..."
#Removing if already added to PATH
PATH=:$PATH:
PATH=${PATH//:${anaconda_bin_path}:/:}
PATH=${PATH#:}; PATH=${PATH%:}
sed -i '/^#<<----/,/#<<------/d' ~/.bash_profile
sed -i '/^# >>>/,/^# <<</d' ~/.bash_profile
#Adding to PATH
echo -e "#<<---- Anaconda Script Entries ---->>" >> ~/.bash_profile
PATH="${PATH:+${PATH}:}${anaconda_bin_path}"
echo -e "PATH=${PATH}" >> ~/.bash_profile
echo -e "export PATH" >> ~/.bash_profile
echo -e "#<<--------------------------------->>" >> ~/.bash_profile
source ~/.bash_profile
export PATH=$PATH
echo -e "$PATH"
echo -e "Anaconda PATH sourced to bash_profile."
echo -e "\nAdd Anaconda to PATH. Completed - [\033[0;32mOK\033[0m]"

conda_ver="$(conda --version)"
echo -e "\nGet conda version. Starting..."
echo -e "[`date --iso-8601=seconds`] - conda version: ${conda_ver}"
echo -e "\nGet conda version. Completed - [\033[0;32mOK\033[0m]"

echo -e "\nInstall python and create virtual env. Starting..."
conda install anaconda-clean -y
conda create -n ${conda_env} ${conda_packages} -y
laststat=$?
if ([ "${laststat}" == 0 ]) then
        echo -e "[`date --iso-8601=seconds`] - Installation successful."
else
        echo -e "[`date --iso-8601=seconds`] - Installation failed. Exiting...\n[\033[0;31mFAILED\033[0m]\n"
        exit
fi
echo -e "\nInstall python and create virtual env. Completed - [\033[0;32mOK\033[0m]"

echo -e "\nHook conda to bash. Starting..."
eval "$(command conda 'shell.bash' 'hook' 2> /dev/null)"
echo -e "\nHook conda to bash completed - [\033[0;32mOK\033[0m]"

echo -e "\nChange conda configs. Starting..."
conda config --set report_errors false
conda config --set auto_activate_base false
echo -e "\nSetting configs completed - [\033[0;32mOK\033[0m]"

echo -e "\nInitialize conda and activate virtual env. Starting..."
conda init bash
conda activate ${conda_env}
laststat=$?
if ([ "${laststat}" == 0 ]) then
        echo -e "[`date --iso-8601=seconds`] - Activating env: ${conda_env} successful."
else
        echo -e "[`date --iso-8601=seconds`] - Activating env: ${conda_env} failed. Exiting...\n[\033[0;31mFAILED\033[0m]\n"
        exit
fi
echo -e "\nInitialize conda and activate virtual env. Completed - [\033[0;32mOK\033[0m]"

echo -e "\nInstall python modules. Starting..."
export https_proxy="http://webproxystatic-on.tsl.telus.com:8080"
pip install ${pip_modules}
laststat=$?
if ([ "${laststat}" == 0 ]) then
        echo -e "[`date --iso-8601=seconds`] - Installation successful."
else
        echo -e "[`date --iso-8601=seconds`] - Installation failed. Exiting...\n[\033[0;31mFAILED\033[0m]\n"
        exit
fi
echo -e "\nInstall python modules. Completed - [\033[0;32mOK\033[0m]"

echo -e "\nDeactivate virtual env. Starting..."
conda deactivate
echo -e "\nVirtual env deactivated - [\033[0;32mOK\033[0m]"

echo -e "\nList virtual envs. Starting..."
conda info --envs
echo -e "\nList virtual envs. Completed - [\033[0;32mOK\033[0m]"

echo -e "\nList packages installed in virtual env: ${conda_env}. Starting..."
conda list -n ${conda_env}
echo -e "\nList packages installed in virtual env: ${conda_env}. Completed - [\033[0;32mOK\033[0m]"

echo -e "\n"
