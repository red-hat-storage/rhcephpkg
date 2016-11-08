_rhcephpkg_commands ()
{
    rhcephpkg --help | sed -e '1,/--help/d' -e 's/ .*//'
}

_rhcephpkg()
{
	local cur="${COMP_WORDS[COMP_CWORD]}"
	local commands=$(_rhcephpkg_commands)
	COMPREPLY=($(compgen -W "$commands" -- ${cur}))
}

complete -F _rhcephpkg rhcephpkg
