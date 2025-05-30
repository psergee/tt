package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/tarantool/tt/cli/cmdcontext"
	"github.com/tarantool/tt/cli/search"
	"github.com/tarantool/tt/cli/uninstall"
)

// newUninstallTtCmd creates a command to install tt.
func newUninstallTtCmd() *cobra.Command {
	tntCmd := &cobra.Command{
		Use:   "tt [version]",
		Short: "Uninstall tt",
		Run:   RunModuleFunc(InternalUninstallModule),
		Args:  cobra.MaximumNArgs(1),
		ValidArgsFunction: func(
			cmd *cobra.Command,
			args []string,
			toComplete string,
		) ([]string, cobra.ShellCompDirective) {
			if len(args) > 0 {
				return []string{}, cobra.ShellCompDirectiveNoFileComp
			}
			return uninstall.GetList(cliOpts, cmd.Name()),
				cobra.ShellCompDirectiveNoFileComp
		},
	}

	return tntCmd
}

// newUninstallTarantoolCmd creates a command to install tarantool.
func newUninstallTarantoolCmd() *cobra.Command {
	tntCmd := &cobra.Command{
		Use:   search.ProgramCe.String() + " [version]",
		Short: "Uninstall tarantool community edition",
		Run:   RunModuleFunc(InternalUninstallModule),
		Args:  cobra.MaximumNArgs(1),
		ValidArgsFunction: func(
			cmd *cobra.Command,
			args []string,
			toComplete string,
		) ([]string, cobra.ShellCompDirective) {
			if len(args) > 0 {
				return []string{}, cobra.ShellCompDirectiveNoFileComp
			}
			return uninstall.GetList(cliOpts, cmd.Name()),
				cobra.ShellCompDirectiveNoFileComp
		},
	}

	return tntCmd
}

// newUninstallTarantoolEeCmd creates a command to install tarantool-ee.
func newUninstallTarantoolEeCmd() *cobra.Command {
	tntCmd := &cobra.Command{
		Use:   search.ProgramEe.String() + " [version]",
		Short: "Uninstall tarantool enterprise edition",
		Run:   RunModuleFunc(InternalUninstallModule),
		Args:  cobra.MaximumNArgs(1),
		ValidArgsFunction: func(
			cmd *cobra.Command,
			args []string,
			toComplete string,
		) ([]string, cobra.ShellCompDirective) {
			if len(args) > 0 {
				return []string{}, cobra.ShellCompDirectiveNoFileComp
			}
			return uninstall.GetList(cliOpts, cmd.Name()),
				cobra.ShellCompDirectiveNoFileComp
		},
	}

	return tntCmd
}

// newUninstallTarantoolDevCmd creates a command to uninstall tarantool-dev.
func newUninstallTarantoolDevCmd() *cobra.Command {
	tntCmd := &cobra.Command{
		Use:   "tarantool-dev",
		Short: "Uninstall tarantool-dev",
		Run:   RunModuleFunc(InternalUninstallModule),
		Args:  cobra.ExactArgs(0),
	}

	return tntCmd
}

// newUninstallTcmCmd creates a command to install tarantool-ee.
func newUninstallTcmCmd() *cobra.Command {
	tntCmd := &cobra.Command{
		Use:   search.ProgramTcm.String() + " [version]",
		Short: "Uninstall tarantool cluster manager",
		Run:   RunModuleFunc(InternalUninstallModule),
		Args:  cobra.MaximumNArgs(1),
		ValidArgsFunction: func(
			cmd *cobra.Command,
			args []string,
			toComplete string,
		) ([]string, cobra.ShellCompDirective) {
			if len(args) > 0 {
				return []string{}, cobra.ShellCompDirectiveNoFileComp
			}
			return uninstall.GetList(cliOpts, cmd.Name()),
				cobra.ShellCompDirectiveNoFileComp
		},
	}

	return tntCmd
}

// NewUninstallCmd creates uninstall command.
func NewUninstallCmd() *cobra.Command {
	uninstallCmd := &cobra.Command{
		Use:   "uninstall",
		Short: "Uninstalls a program",
		Example: `
# To uninstall Tarantool:

    $ tt uninstall tarantool <version>`,
	}

	uninstallCmd.AddCommand(
		newUninstallTtCmd(),
		newUninstallTarantoolCmd(),
		newUninstallTarantoolEeCmd(),
		newUninstallTarantoolDevCmd(),
		newUninstallTcmCmd(),
	)

	return uninstallCmd
}

// InternalUninstallModule is a default uninstall module.
func InternalUninstallModule(cmdCtx *cmdcontext.CmdCtx, args []string) error {
	if !isConfigExist(cmdCtx) {
		return errNoConfig
	}

	program, err := search.ParseProgram(cmdCtx.CommandName)
	if err != nil {
		return fmt.Errorf("failed to uninstall: %w", err)
	}

	programVersion := ""
	if len(args) == 1 {
		programVersion = args[0]
	}

	return uninstall.UninstallProgram(program, programVersion, cliOpts.Env.BinDir,
		cliOpts.Env.IncludeDir+"/include", cmdCtx)
}
