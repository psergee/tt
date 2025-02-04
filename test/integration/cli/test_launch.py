import os
import shutil
import subprocess
import tempfile

import pytest
import yaml

from utils import (config_name, create_external_module, create_tt_config,
                   run_command_and_get_output)

# Some of the tests below should check the behavior
# of modules that have an internal implementation.
# `version` module is the lightest module, so we test using it.


# ##### #
# Tests #
# ##### #
def test_local_launch(tt_cmd, tmpdir):
    module = "version"
    cmd = [tt_cmd, "-L", tmpdir, module]

    # No configuration file specified.
    assert subprocess.run(cmd).returncode == 1

    # With the specified config file.
    create_tt_config(tmpdir, tmpdir)
    module_message = create_external_module(module, tmpdir)

    rc, output = run_command_and_get_output(cmd, cwd=os.getcwd())
    assert rc == 0
    assert module_message in output


def test_local_launch_find_cfg(tt_cmd, tmpdir):
    module = "version"

    # Find tt.yaml at cwd parent.
    tmpdir_without_config = tempfile.mkdtemp(dir=tmpdir)
    cmd = [tt_cmd, "-L", tmpdir_without_config, module]

    create_tt_config(tmpdir, tmpdir)
    module_message = create_external_module(module, tmpdir)

    rc, output = run_command_and_get_output(cmd, cwd=os.getcwd())
    assert rc == 0
    assert module_message in output


def test_local_launch_find_cfg_modules_relative_path(tt_cmd, tmpdir):
    module = "version"

    # Find tt.yaml at cwd parent.
    tmpdir_without_config = tempfile.mkdtemp(dir=tmpdir)
    cmd = [tt_cmd, module]

    modules_dir = os.path.join(tmpdir, "ext_modules")
    os.mkdir(modules_dir)
    create_tt_config(tmpdir, os.path.join(".", "ext_modules"))
    module_message = create_external_module(module, modules_dir)

    rc, output = run_command_and_get_output(cmd, cwd=tmpdir_without_config)
    assert rc == 0
    assert module_message in output


def test_local_launch_non_existent_dir(tt_cmd, tmpdir):
    module = "version"
    cmd = [tt_cmd, "-L", "non-exists-dir", module]
    rc, output = run_command_and_get_output(cmd, cwd=tmpdir)

    assert rc == 1
    assert "failed to change working directory" in output


# This test looking for tt.yaml from cwd to root (without -L flag).
def test_default_launch_find_cfg_at_cwd(tt_cmd, tmpdir):
    module = "version"
    module_message = create_external_module(module, tmpdir)

    # Find tt.yaml at current work directory.
    create_tt_config(tmpdir, tmpdir)

    cmd = [tt_cmd, module]
    rc, output = run_command_and_get_output(cmd, cwd=tmpdir)
    assert rc == 0
    assert module_message in output


def test_default_launch_find_cfg_at_parent(tt_cmd, tmpdir):
    module = "version"
    module_message = create_external_module(module, tmpdir)

    create_tt_config(tmpdir, tmpdir)
    cmd = [tt_cmd, module]

    # Find tt.yaml at cwd parent.
    tmpdir_without_config = tempfile.mkdtemp(dir=tmpdir)
    rc, output = run_command_and_get_output(cmd, cwd=tmpdir_without_config)
    assert rc == 0
    assert module_message in output


def test_launch_local_tt_executable(tt_cmd, tmpdir):
    # We check if exec works on the local tt executable.
    # In the future, the same should be done when checking the
    # local Tarantool executable, but so far this is impossible.
    create_tt_config(tmpdir, tmpdir)
    os.mkdir(tmpdir + "/bin")

    tt_message = "Hello, I'm CLI exec!"
    with open(os.path.join(tmpdir, "bin/tt"), "w") as f:
        f.write(f"#!/bin/sh\necho \"{tt_message}\"")

    # tt found but not executable - there should be an error.
    commands = [
        [tt_cmd, "version"],
        [tt_cmd, "-L", tmpdir, "version"],
        [tt_cmd, "version", "--cfg", os.path.join(tmpdir, config_name)]
    ]

    for cmd in commands:
        rc, output = run_command_and_get_output(cmd, cwd=tmpdir)
        assert rc == 1
        assert "permission denied" in output

    # tt found and executable.
    os.chmod(os.path.join(tmpdir, "bin/tt"), 0o777)
    for cmd in commands:
        rc, output = run_command_and_get_output(cmd, cwd=tmpdir)
        assert rc == 0
        assert tt_message in output


def test_launch_local_tt_executable_in_parent_dir(tt_cmd, tmpdir):
    create_tt_config(tmpdir, tmpdir)
    os.mkdir(tmpdir + "/bin")

    tt_message = "Hello, I'm CLI exec!"
    with open(os.path.join(tmpdir, "bin/tt"), "w") as f:
        f.write(f"#!/bin/sh\necho \"{tt_message}\"")

    commands = [
        [tt_cmd, "version"],
        [tt_cmd, "-L", tmpdir, "version"]
    ]

    tmpdir_without_config = tempfile.mkdtemp(dir=tmpdir)
    os.chmod(os.path.join(tmpdir, "bin/tt"), 0o777)
    for cmd in commands:
        rc, output = run_command_and_get_output(cmd, cwd=tmpdir_without_config)
        assert rc == 0
        assert tt_message in output


def test_launch_local_tt_executable_relative_bin_dir(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))

    tt_message = "Hello, I'm CLI exec!"
    with open(os.path.join(tmpdir, "binaries/tt"), "w") as f:
        f.write(f"#!/bin/sh\necho \"{tt_message}\"")
    os.chmod(os.path.join(tmpdir, "binaries", "tt"), 0o777)

    commands = [
        [tt_cmd, "version"],
        [tt_cmd, "-L", tmpdir, "version"]
    ]

    with tempfile.TemporaryDirectory(dir=tmpdir) as tmp_working_dir:
        for cmd in commands:
            rc, output = run_command_and_get_output(cmd, cwd=tmp_working_dir)
            assert rc == 0
            assert tt_message in output


def test_launch_local_tt_missing_executable(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))

    commands = [
        [tt_cmd, "version"],
        [tt_cmd, "-L", tmpdir, "version"],
        [tt_cmd, "--cfg", config_path, "version"]
    ]

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        for cmd in commands:
            rc, output = run_command_and_get_output(cmd, cwd=tmp_working_dir)
            # No error. Current tt is executed.
            assert rc == 0
            assert "Tarantool CLI version" in output


def test_launch_local_tarantool(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))
    tarantool_message = "Hello, I'm Tarantool"
    with open(os.path.join(tmpdir, "binaries/tarantool"), "w") as f:
        f.write(f"#!/bin/sh\necho \"{tarantool_message}\"")
    os.chmod(os.path.join(tmpdir, "binaries/tarantool"), 0o777)

    commands = [
        [tt_cmd, "-L", tmpdir, "run", "--version"],
        [tt_cmd, "--cfg", config_path, "run", "--version"]
    ]

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        for cmd in commands:
            rc, output = run_command_and_get_output(cmd, cwd=tmp_working_dir)
            assert rc == 0
            assert tarantool_message in output


def test_launch_local_tarantool_missing_in_bin_dir(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))

    commands_intmp = [
        [tt_cmd, "run", "--version"],
    ]

    commands_external = [
        [tt_cmd, "-L", tmpdir, "run", "--version"],
        [tt_cmd, "--cfg", config_path, "run", "--version"]
    ]

    for cmd in commands_intmp:
        rc, output = run_command_and_get_output(cmd, cwd=tmpdir)
        # Missing binaries is not a error. Default Tarantool is used.
        assert rc == 0
        assert "Tarantool" in output

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        for cmd in commands_external:
            rc, output = run_command_and_get_output(cmd, cwd=tmp_working_dir)
            # Missing binaries is not a error. Default Tarantool is used.
            assert rc == 0
            assert "Tarantool" in output


def test_launch_local_launch_tarantool_with_config_in_parent_dir(tt_cmd, tmpdir):
    tmpdir_without_config = tempfile.mkdtemp(dir=tmpdir)
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))
    tarantool_message = "Hello, I'm Tarantool"
    with open(os.path.join(tmpdir, "binaries/tarantool"), "w") as f:
        f.write(f"#!/bin/sh\ntouch file.txt\necho \"{tarantool_message}\"")
    os.chmod(os.path.join(tmpdir, "binaries/tarantool"), 0o777)

    commands = [
        [tt_cmd, "-L", tmpdir_without_config, "run", "--version"],
    ]

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        for cmd in commands:
            rc, output = run_command_and_get_output(cmd, cwd=tmp_working_dir)
            assert rc == 0
            assert tarantool_message in output
            assert os.path.exists(os.path.join(tmpdir_without_config, "file.txt"))


def test_launch_local_launch_tarantool_with_yml_config_in_parent_dir(tt_cmd, tmpdir):
    tmpdir_without_config = tempfile.mkdtemp(dir=tmpdir)
    config_path = os.path.join(tmpdir, config_name.replace("yaml", "yml"))
    with open(config_path, "w") as f:
        yaml.dump({"env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))
    tarantool_message = "Hello, I'm Tarantool"
    with open(os.path.join(tmpdir, "binaries/tarantool"), "w") as f:
        f.write(f"#!/bin/sh\ntouch file.txt\necho \"{tarantool_message}\"")
    os.chmod(os.path.join(tmpdir, "binaries/tarantool"), 0o777)

    commands = [
        [tt_cmd, "-L", tmpdir_without_config, "run", "--version"],
    ]

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        for cmd in commands:
            rc, output = run_command_and_get_output(cmd, cwd=tmp_working_dir)
            assert rc == 0
            assert tarantool_message in output
            assert os.path.exists(os.path.join(tmpdir_without_config, "file.txt"))


def test_launch_system_tarantool(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"modules": {"directory": f"{tmpdir}"},
                   "env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))
    tarantool_message = "Hello, I'm Tarantool"
    with open(os.path.join(tmpdir, "binaries/tarantool"), "w") as f:
        f.write(f"#!/bin/sh\necho \"{tarantool_message}\"")
    os.chmod(os.path.join(tmpdir, "binaries/tarantool"), 0o777)

    command = [tt_cmd, "-S", "run"]

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        with open(os.path.join(tmp_working_dir, config_name), "w") as f:
            yaml.dump({"modules": {"directory": f"{tmpdir}"},
                       "env": {"bin_dir": ""}}, f)
        my_env = os.environ.copy()
        my_env["TT_SYSTEM_CONFIG_DIR"] = tmpdir
        rc, output = run_command_and_get_output(command, cwd=tmp_working_dir, env=my_env)
        assert rc == 0
        assert tarantool_message in output


def test_launch_system_tarantool_yml_system_config(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name.replace("yaml", "yml"))
    with open(config_path, "w") as f:
        yaml.dump({"modules": {"directory": f"{tmpdir}"},
                   "env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))
    tarantool_message = "Hello, I'm Tarantool"
    with open(os.path.join(tmpdir, "binaries/tarantool"), "w") as f:
        f.write(f"#!/bin/sh\necho \"{tarantool_message}\"")
    os.chmod(os.path.join(tmpdir, "binaries/tarantool"), 0o777)

    command = [tt_cmd, "-S", "run"]

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        with open(os.path.join(tmp_working_dir, config_name.replace("yaml", "yml")), "w") as f:
            yaml.dump({"tt": {"modules": {"directory": f"{tmpdir}"},
                       "env": {"bin_dir": ""}}}, f)
        my_env = os.environ.copy()
        my_env["TT_SYSTEM_CONFIG_DIR"] = tmpdir
        rc, output = run_command_and_get_output(command, cwd=tmp_working_dir, env=my_env)
        assert rc == 0
        assert tarantool_message in output


def test_launch_system_tarantool_missing_executable(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"modules": {"directory": f"{tmpdir}"},
                   "env": {"bin_dir": "./binaries"}}, f)

    command = [tt_cmd, "-S", "run", "--version"]

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        my_env = os.environ.copy()
        my_env["TT_SYSTEM_CONFIG_DIR"] = tmpdir
        rc, output = run_command_and_get_output(command, cwd=tmp_working_dir, env=my_env)
        assert rc == 0
        assert "Tarantool" in output


def test_launch_system_config_not_loaded_if_local_enabled(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"env": {"bin_dir": "./binaries"}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))
    tarantool_message = "Hello, I'm Tarantool"
    with open(os.path.join(tmpdir, "binaries/tarantool"), "w") as f:
        f.write(f"#!/bin/sh\necho \"{tarantool_message}\"")
    os.chmod(os.path.join(tmpdir, "binaries/tarantool"), 0o777)

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        command = [tt_cmd, "-L", tmp_working_dir, "run", "--version"]
        my_env = os.environ.copy()
        my_env["TT_SYSTEM_CONFIG_DIR"] = tmpdir
        rc, output = run_command_and_get_output(command, cwd=tmp_working_dir, env=my_env)
        assert rc == 1
        assert "failed to find Tarantool CLI config for " in output


def test_launch_system_config_not_loaded_if_cfg_specified_is_missing(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"tt": {"env": {"bin_dir": "./binaries"}}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))
    tarantool_message = "Hello, I'm Tarantool"
    with open(os.path.join(tmpdir, "binaries/tarantool"), "w") as f:
        f.write(f"#!/bin/sh\necho \"{tarantool_message}\"")
    os.chmod(os.path.join(tmpdir, "binaries/tarantool"), 0o777)

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        command = [tt_cmd, "-c", os.path.join(tmp_working_dir, config_name), "run",
                   "--version"]
        my_env = os.environ.copy()
        my_env["TT_SYSTEM_CONFIG_DIR"] = tmpdir
        rc, output = run_command_and_get_output(command, cwd=tmp_working_dir, env=my_env)
        assert rc == 1
        assert "Failed to configure Tarantool CLI" in output


def test_launch_ambiguous_config_opts(tt_cmd, tmpdir):
    config_path = os.path.join(tmpdir, config_name)
    with open(config_path, "w") as f:
        yaml.dump({"tt": {"env": {"bin_dir": "./binaries"}}}, f)

    os.mkdir(os.path.join(tmpdir, "binaries"))

    commands = [
        [tt_cmd, "--cfg", config_path, "-L", tmpdir, "run", "--version"],
        [tt_cmd, "--cfg", config_path, "-S", "run", "--version"],
        [tt_cmd, "-S", "-L", tmpdir, "run", "--version"],
    ]

    with tempfile.TemporaryDirectory() as tmp_working_dir:
        for cmd in commands:
            rc, output = run_command_and_get_output(cmd, cwd=tmp_working_dir)
            assert rc == 1
            assert "you can specify only one of" in output


def test_external_module_without_internal_implementation(tt_cmd, tmpdir):
    # Create an external module, which don't have internal
    # implementation.
    module = "abc-example"
    module_message = create_external_module(module, tmpdir)
    create_tt_config(tmpdir, tmpdir)

    cmd = [tt_cmd, module]
    rc, output = run_command_and_get_output(cmd, cwd=tmpdir)
    assert rc == 0
    assert module_message in output

    # Trying to start external module with -I flag.
    # In this case, tt should ignore this flag and just
    # start module.
    cmd = [tt_cmd, "-I", module]
    rc, output = run_command_and_get_output(cmd, cwd=tmpdir)
    assert rc == 0
    assert module_message in output


def test_launch_with_cfg_flag(tt_cmd, tmpdir):
    module = "version"

    # Send non existent config path.
    non_exist_cfg_tmpdir = tempfile.mkdtemp(dir=tmpdir)
    cmd = [tt_cmd, "--cfg", "non-exists-path", module]
    rc, output = run_command_and_get_output(cmd, cwd=non_exist_cfg_tmpdir)
    assert rc == 1
    assert "specified path to the configuration file is invalid" in output

    # Create one more temporary directory
    exists_cfg_tmpdir = tempfile.mkdtemp(dir=tmpdir)
    module_message = create_external_module(module, exists_cfg_tmpdir)
    config_path = create_tt_config(exists_cfg_tmpdir, exists_cfg_tmpdir)

    cmd = [tt_cmd, "--cfg", config_path, module]
    rc, output = run_command_and_get_output(cmd, cwd=tmpdir)
    assert rc == 0
    assert module_message in output


@pytest.mark.parametrize("module", ["version", "non-exists-module"])
def test_launch_external_cmd_with_flags(tt_cmd, tmpdir, module):
    module_message = create_external_module(module, tmpdir)
    create_tt_config(tmpdir, tmpdir)

    cmd = [tt_cmd, module, "--non-existent-flag", "-f", "argument1"]
    rc, output = run_command_and_get_output(cmd, cwd=tmpdir)
    assert rc == 0
    assert module_message in output


def test_std_err_stream_local_launch_non_existent_dir(tt_cmd, tmpdir):
    module = "version"
    cmd = [tt_cmd, "-L", "non-exists-dir", module]
    tt_process = subprocess.Popen(
        cmd,
        cwd=tmpdir,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True
    )
    tt_process.stdin.close()
    tt_process.wait()
    assert tt_process.returncode == 1
    assert "failed to change working directory" not in tt_process.stdout.readline()
    assert "failed to change working directory" in tt_process.stderr.readline()


def test_launch_with_env_cfg(tt_cmd):
    cmd = [tt_cmd, "cfg", "dump"]

    tmpdir_with_env_config = tempfile.mkdtemp()
    tmpdir_with_flag_config = tempfile.mkdtemp()
    try:
        # Test 'TT_CLI_CFG' env. variable.
        env_config_path = tmpdir_with_env_config + "/tt.yaml"
        with open(env_config_path, "w") as f:
            yaml.dump({"env": {"bin_dir": "foo/binaries"}}, f)
        test_env = os.environ.copy()
        test_env['TT_CLI_CFG'] = env_config_path

        rc, output = run_command_and_get_output(cmd, cwd=os.getcwd(), env=test_env)
        expected_bin_dir = "bin_dir: " + tmpdir_with_env_config + "/foo/binaries"
        assert rc == 0
        assert expected_bin_dir in output

        # Test that '-c' flag has higher priority than 'TT_CLI_CFG'.
        flag_config_path = tmpdir_with_flag_config + "/tt.yaml"
        with open(flag_config_path, "w") as f:
            yaml.dump({"env": {"bin_dir": "foo/my_cool_binaries"}}, f)
        cmd = [tt_cmd, "-c", flag_config_path, "cfg", "dump"]

        rc, output = run_command_and_get_output(cmd, cwd=os.getcwd(), env=test_env)
        expected_bin_dir = "bin_dir: " + tmpdir_with_flag_config + "/foo/my_cool_binaries"
        assert rc == 0
        assert expected_bin_dir in output
    finally:
        shutil.rmtree(tmpdir_with_env_config)
        shutil.rmtree(tmpdir_with_flag_config)


def test_launch_with_invalid_env_cfg(tt_cmd):
    cmd = [tt_cmd, "cfg", "dump"]

    # Set invalid 'TT_CLI_CFG' env. variable.
    test_env = os.environ.copy()
    test_env['TT_CLI_CFG'] = "foo/bar"

    rc, output = run_command_and_get_output(cmd, cwd=os.getcwd(), env=test_env)
    assert rc == 1
    assert "specified path to the configuration file is invalid" in output


def test_launch_with_verbose_output(tt_cmd, tmpdir):
    tmpdir_with_flag_config = tempfile.mkdtemp()
    try:
        create_tt_config(tmpdir_with_flag_config, tmpdir)
        cmd = [tt_cmd, "-c", tmpdir_with_flag_config + "/tt.yaml", "-V", "-h"]

        rc, output = run_command_and_get_output(cmd, cwd=os.getcwd())
        assert rc == 0
        assert tmpdir_with_flag_config + "/tt.yaml" in output
    finally:
        shutil.rmtree(tmpdir_with_flag_config)
