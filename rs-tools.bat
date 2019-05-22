@echo off
@setlocal enabledelayedexpansion
@setlocal enableextensions

REM ============================================================================
REM sci-move.bat: move downloaded files from temp system folder ----------------
REM ============================================================================

goto :label-initialization

REM initialization -------------------------------------------------------------
:label-initialization

    REM settings --------------------------------------------
    set "fun-venv-activate=%SHARED_VENV%\sci-py\Scripts\activate.bat"  

goto :label-definitions

REM definitions ----------------------------------------------------------------
REM ============================================================================
:label-definitions

    REM files and folders ------------------------------------------------------
    set "folder-temp=%TEMP%\sci-lib\"
        if not exist !folder-temp! mkdir !folder-temp!
   
    REM functions --------------------------------------------------------------
    set "fun-read-ini=%~dp0batch\read-ini.bat"
    set "fun-get-file-ext=%~dp0batch\tools-get-file-ext.bat"

    REM executable -------------------------------------------------------------
    set "fun-python-venv=python.exe" 
    set "fun-rs-show=%~dp0python\rs-show.py"
    set "fun-venv-deactivate=deactivate"

    REM input properties -------------------------------------------------------
    set "arg.options-next=dir task"
    set "arg.options-switch=help new-label"
    REM for /f "usebackq tokens=*" %%a in (`call "!fun-read-ini!" /i "workspace-names" "!file-project!"`) do (
    REM     set "arg.workspaces=%%~a"
    REM )

    set "arg.elem=!arg.options-switch! !arg.options-next!"

goto :label-input-arguments
REM definitions ----------------------------------------------------------------
REM ============================================================================
:label-definitions

REM input arguments ------------------------------------------------------------
REM ============================================================================
:label-input-arguments

    REM initialization ---------------------------------------------------------
    set "next="
    set "ext="

    if "%1"=="" goto usage
    REM evalutation ------------------------------------------------------------
    for %%i in (%*) do (
        set "input.raw=%%~i" & set "input.prop=!input.raw:~+1!"
        REM get following element of input properties --------------------------
        if defined next (
            REM get following element of input properties ----------------------
            for %%j in (!arg.options-next!) do (
                if "%%j"=="!next!" set "arg.!next!=!input.raw!" & set "next=" 
            )
        )
        REM get input property or elements without preceding input property ----
        if not defined next (
            REM get input property ---------------------------------------------
            for %%j in (!arg.elem!) do (
                if "%%j"=="!input.prop!" (   
                    for %%k in (help) do if "%%k"=="!input.prop!" goto usage
                    for %%k in (!arg.options-next!) do if "%%k"=="!input.prop!" set "next=!input.prop!"
                    for %%k in (!arg.options-switch!) do if "%%k"=="!input.prop!" set "arg.!input.prop!=!input.prop!"

                    set "arg.elem-flag=true"
                )
            )
            REM get element without a preceding input property -----------------
            if not "!arg.elem-flag!"=="true" set "arg.dir=%~1"
        )
    )

    if defined arg.help goto :label-usage

    if defined arg.verbose echo Arguments: %* & echo. & REM @note[verbose]

    REM evaluate file/directory specification ----------------------------------
    set "file-source=!arg.dir!"
    if defined file-source set "file-source.isdefined=true"

    if defined file-source (
        for /f "tokens=1,* delims=:" %%a in ("!file-source!") do (
            if "%%~b"=="" set "file-source=!cd!!file-source:~+1!"
        )

        call "!fun-get-file-ext!" "!file-source!" file-source.dir file-source.name file-source.ext file-source.namex 

        if defined arg.verbose echo Image file: !file-source.dir! !file-source.name! !file-source.ext! & echo. & REM @note[verbose]

        if not defined file-source.name set "file-source.isdir=true"

        if defined arg.config set "file-source.name=!arg.config!"
    )

goto :label-process

REM process --------------------------------------------------------------------
REM ============================================================================
:label-process

    REM activating virtual environment -----------------------------------------
    call "!fun-venv-activate!"

    REM initialize config folder -----------------------------------------------
    set "file-config.dir=!file-source.dir!.config\"
    set "file-config=!file-config.dir!settings.data.ini"
    set "file-config-label=!file-config.dir!settings.label.ini"  

    REM Validate task ----------------------------------------------------------
    set "task.name=!arg.task!"
    if not defined task.name echo Task not defined & goto :label-end & REM @note[error]
    for /f "tokens=*" %%i in ('"call !fun-read-ini! /i data /s general !file-config!"') do (
        for %%j in (%%i) do if "%%j"=="!task.name!" set "task.defined=true" 
    )

    if not defined task.defined echo Task not known & goto :label-end & REM @note[error]

    set "file-source.dir=!file-source.dir!!task.name!\"

    REM Get folders ------------------------------------------------------------
    for /f "tokens=*" %%i in ('"call !fun-read-ini! /i data /s !task.name! !file-config!"') do (
        set "idx=0"
        for %%j in (%%i) do (
            set "file-source.folders[!idx!]=%%j"

            set /a "idx=!idx!+1"
        ) 
        set /a "idx=!idx!-1"
        set "file-source.folders-length=!idx!"
    )

    set "fun-rs-show.arg="
    for /l %%i in (0,1,!file-source.folders-length!) do (

        set "file-temp=!file-config.dir!files.!file-source.folders[%%i]!.txt"
        if not exist !file-temp! (
            type nul > !file-temp!
            set "idx=0"
            set "folder-temp=!file-source.dir!!file-source.folders[%%i]!\"
            for /f %%j in ('"dir /b /a:-d !folder-temp!"') do (
                echo !folder-temp!%%j >> !file-temp!

                set /a "idx=!idx!+1"
            )
            set /a "idx=!idx!-1"
            set "file-source.folders-number=!idx!"
        )

        set "fun-rs-show.arg=!fun-rs-show.arg! --!file-source.folders[%%i]!"
        set "fun-rs-show.arg=!fun-rs-show.arg! !file-temp!"

        if "!file-source.folders[%%i]!"=="label" (

            set "file-temp=!file-config.dir!config.!file-source.folders[%%i]!.txt"
            if defined arg.new-label (
                type nul > !file-temp! 
                for /f "tokens=*" %%j in ('"call !fun-read-ini! /i labels /s label !file-config!"') do (
                    for %%k in (%%j) do (
                        set "label.name=%%k"
                        
                        for /f "tokens=*" %%l in ('"call !fun-read-ini! /i !label.name! /s label !file-config!"') do (
                            set "label.index=%%~l"
                        )
                        for /f "tokens=*" %%l in ('"call !fun-read-ini! /i color /s !label.name! !file-config-label!"') do (
                            set "label.color=%%~l"
                        )

                        echo !label.name! !label.index! !label.color! >> !file-temp!
                    )
                )
            )
                        
            set "fun-rs-show.arg=!fun-rs-show.arg! --labels_color"
            set "fun-rs-show.arg=!fun-rs-show.arg! !file-temp!"
        )
    )

    call "!fun-python-venv!" "!fun-rs-show!" !fun-rs-show.arg!
    
goto :label-end

REM label-end-------------------------------------------------------------------
REM ============================================================================
:label-end

    if exist "X" del X
    
    call "!fun-venv-deactivate!"
    
goto :eof

REM tools ----------------------------------------------------------------------
REM ============================================================================

    REM print specific symbols -------------------------------------------------
    REM @uri[help]: https://stackoverflow.com/a/5344911/1683264
    :c
        set "param=^%~2" !
        set "param=!param:"=\"!"
        findstr /p /A:%1 "." "!param!\..\X" nul
        <nul set /p ".=%DEL%%DEL%%DEL%%DEL%%DEL%%DEL%%DEL%"
    exit /b
    :s
        <NUL set /p "=/"&exit /b

REM usage ----------------------------------------------------------------------
REM ============================================================================
:usage

    REM print specific symbols  ------------------------------------------------
    for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set "DEL=%%a"
    <nul > X set /p ".=."

    REM usage  -----------------------------------------------------------------
    call :c 0F "Usage: %~nx0" & echo;  & echo;
    call :c 0F "    -h, -help"&echo;
    echo        Displays help

goto :label-end
