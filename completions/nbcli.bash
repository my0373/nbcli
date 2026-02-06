#!/usr/bin/env bash

_nbcli_completions()
{
    local cur prev words cword
    _init_completion -s || return

    local global_opts="--timeout --insecure --plain --json --yaml --csv -h --help"
    local commands="status get list dump"

    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
        return
    fi

    case "${words[1]}" in
        get)
            local get_opts="--param --filter --path"
            COMPREPLY=( $(compgen -W "${get_opts} ${global_opts}" -- "${cur}") )
            ;;
        list)
            local list_opts="--param --filter --path --all"
            COMPREPLY=( $(compgen -W "${list_opts} ${global_opts}" -- "${cur}") )
            ;;
        dump)
            local dump_opts="--include-all"
            COMPREPLY=( $(compgen -W "${dump_opts} ${global_opts}" -- "${cur}") )
            ;;
        *)
            COMPREPLY=( $(compgen -W "${global_opts}" -- "${cur}") )
            ;;
    esac
}

complete -F _nbcli_completions nbcli
