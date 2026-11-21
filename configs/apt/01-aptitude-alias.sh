# ==============================================================================
# VYRON Micro-OS System-Wide Package Manager Alias
# ==============================================================================
# Forces 'apt' and 'apt-get' invocations to execute through aptitude
alias apt='/usr/bin/aptitude'
alias apt-get='/usr/bin/aptitude'
export APT_CONFIG="/etc/apt/apt.conf.d/99vyron"
