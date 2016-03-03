import os
import click


def to_bool(value):
    return {'true': True, 'false': False}[value.lower()]
specs = __builtins__.copy()
specs['bool'] = to_bool


class Config(object):

    def __init__(self):
        self.verbose = False
        self.debug = False
        self.directory = ""
        self.default_verbose = False
        self.default_debug = False
        self._verbose_spec = "bool"
        self._debug_spec = "bool"
        self.default_directory = "~/"
        self.default_list = "default"
        self.config = "~/.odoconfig"
        self.default_positions = False
        self._paths = {}
        self._lists = {}

    def initialise_defaults(self):
        try:
            with open(os.path.expanduser(self.config), 'r') as fh:
                for l in fh.readlines():
                    if l.startswith('default'):
                        name, value, spec = l.split('=')
                        try:
                            setattr(
                                self,
                                name, 
                                specs.get(spec.strip(), str)(value)
                            )
                            if self.debug:
                                click.secho(
                                    'Set {0} to {1}.'
                                    .format(name, value), 
                                    fg="cyan"
                                )
                        except TypeError:
                            if self.debug:
                                click.secho(
                                    'Unable to convert {0} to {1}.'
                                    .format(name, spec),
                                    fg="red"
                                )
                            continue
        except (IOError, OSError):
            if self.debug:
                click.secho('Config file does not yet exist.', fg="red")

    @staticmethod
    def spec_name(name):
        return name.split('default')[1] + '_spec'

    def reset_defaults(self):
        try:    
            with open(os.path.expanduser(self.config), 'w') as fh:
                pass
        except (IOError, OSError):
            if self.debug:
                click.secho('Error writing to config file.', fg="red")

    def set_default(self, name, value, spec=None):
        if name.startswith('default'):
            setattr(self, name, value)
            if self.debug:
                click.secho(
                    'Set {0} to {1}.'
                    .format(name, value), 
                    fg="cyan"
                )
            if spec is not None:
                setattr(self, self.spec_name(name), spec)
                if self.debug:
                    click.secho(
                        'Set {0} to {1}.'
                        .format(name, value), 
                        fg="cyan"
                    )
        try:
            with open(os.path.expanduser(self.config), 'w') as fh:
                for default in dir(self):
                    if default.startswith('default'):
                        default_string = "{d}={v}={s}\n".format(
                            d=default, 
                            v=getattr(self, default),
                            s=getattr(self, self.spec_name(default), "str")
                        )
                        fh.write(default_string)
                        if self.debug:
                            click.secho(
                                'Wrote {0} to file.'
                                .format(default_string.strip()),
                                fg="cyan"
                            )
        except (IOError, OSError):
            if self.debug:
                click.secho('Error writing to config file.', fg="red")

    def path(self, list_name=None):
        if list_name is not None:
            if list_name in self._paths:
                if self.debug:
                    click.secho(
                        "Using path cache for \"{}\"."
                        .format(list_name),
                        fg="cyan"
                    )
                path = self._paths[list_name]
            else:
                if self.debug:
                    click.secho(
                        "Setting path cache for \"{}\"."
                        .format(list_name),
                        fg="cyan"
                    )
                path = os.path.expanduser(
                    "{dir}{sl}.{name}.odo"
                    .format(
                        dir=self.directory,
                        name=list_name,
                        sl="" if self.directory.endswith('/') else "/",
                    )
                )
                self._paths[list_name] = path
            return path
        else:
            return os.path.expanduser(self.directory)

    def find_lists(self):
        try:
            list_names = [
                file_name[1:-len('.odo')]
                for file_name in os.listdir(self.path())
                if file_name.endswith('.odo')
            ]
            for name in list_names:
                if self.debug:
                    click.secho(
                        "Setting path cache for \"{}\"."
                        .format(name),
                        fg="cyan"
                    )
                self._paths[name] = os.path.expanduser(
                    "{dir}{sl}.{name}.odo"
                    .format(
                        dir=self.directory,
                        name=name,
                        sl="" if self.directory.endswith('/') else "/",
                    )
                )
            return list_names
        except OSError:
            if self.verbose:
                click.echo("Not a directory.")
            return []

    def read(self, list_name, force=False):
        if list_name not in self._lists or force:
            try:
                with open(self.path(list_name), 'r') as fh:
                    if self.debug:
                        click.secho("Opened file.", fg="cyan")
                    self._lists[list_name] = fh.readlines()
                    if self.debug:
                        click.secho(
                            "Set list cache for \"{}\"."
                            .format(list_name),
                            fg="cyan"
                        )
            except (IOError, OSError):
                if self.verbose:
                    click.secho("Failed to read list.", fg="red")
                return None
        elif self.debug:
            click.secho(
                "Using list cache for \"{}\"."
                .format(list_name),
                fg="cyan"
            )
        return self._lists[list_name]

    def get_item_count(self, list_name):
        lists = self.read(list_name)
        return len(lists) if lists is not None else None

    def remove(self, list_name, item_name):
        if list_name in self._lists:
            self._lists[list_name] = [
                item
                for item in self._lists[list_name]
                if item != item_name
            ]

    def rename_list(self, list_name, list_new_name):
        if list_name in self._lists:
            self._lists[list_new_name] = self._lists.pop(list_name)


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option('--list-dir', default=None, help="This is the directory of lists.")
@pass_config
def cli(config, verbose, debug, list_dir):
    config.initialise_defaults()
    if verbose or config.default_verbose:
        click.echo('Defaults initialised.')
    
    config.verbose = verbose | bool(config.default_verbose)
    config.debug = debug | bool(config.default_debug)    
    config.directory = list_dir or config.default_directory

    if debug or config.default_debug:
        click.secho(
            'Verbose set to {0}.'
            .format(config.verbose), 
            fg="cyan"
        )
        click.secho(
            'Debug set to {0}.'
            .format(config.debug), 
            fg="cyan"
        )
        click.secho(
            'Directory set to {0}.'
            .format(config.directory), 
            fg="cyan"
        )
    

@cli.command()
@click.argument('name')
@click.argument('value')
@click.argument('spec', default="")
@pass_config
def set(config, name, value, spec):
    config.set_default('default_{0}'.format(name), value, spec or None)


@cli.command()
@pass_config
def reset(config):
    config.reset_defaults()


@cli.command()
@pass_config
def defaults(config):
    for default in dir(config):
        if default.startswith('default'):
            click.echo('{0}: {1}'.format(
                default,
                getattr(config, default)
            ))


@cli.command()
@click.argument('name', default='')
@click.option('--positions', is_flag=True)
@pass_config
def list(config, name, positions):
    name = name or config.default_list
    if config.verbose:
        click.echo(
            "Listing items from \"{ln}\"."
            .format(ln=name)
        )

    if not os.path.exists(config.path(name)):
        click.echo("List does not exist.")
        return

    items = config.read(name)
    if items is not None:
        if not items:
            click.echo("List empty.")
        if positions or config.default_positions:
            for p, item in enumerate(items):
                click.echo("{0}: {1}".format(p, item.rstrip()))
        else:
            for item in items:
                click.echo(">> {0}".format(item.rstrip()))
        if config.verbose:
            click.echo("Done.")


@cli.command()
@click.option('--lol', is_flag=True)
@click.option('--paths', is_flag=True)
@click.option('--positions', is_flag=True)
@pass_config
def lists(config, lol, paths, positions):
    if config.verbose:
        click.echo(
            "Listing all lists found at {dir}."
            .format(dir=config.path())
        )
    for name in config.find_lists():
        count = config.get_item_count(name)
        if count is not None:
            click.echo(
                "> {name} [{count} items]"
                .format(
                    name="{0}".format(config.path(name)) if paths else name,
                    count=count,
                )
            )
            if lol:
                if config.verbose:
                    click.echo(
                        "Listing items from \"{ln}\"."
                        .format(ln=name)
                    )
                if positions or config.default_positions:
                    for p, item in enumerate(config.read(name)):
                        click.echo("{0}: {1}".format(p, item.rstrip()))
                else:
                    for item in config.read(name):
                        click.echo(">> {0}".format(item.rstrip()))
        if config.verbose:
            click.echo("Done.")


@cli.command()
@click.argument('name', default='')
@click.option('--delete', is_flag=True)
@click.option('--all-lists', is_flag=True)
@pass_config
def clear(config, name, delete, all_lists):
    name = name or config.default_list
    for name in config.find_lists() if all_lists else [name]:

        if config.verbose:
            click.echo(
                "Clearing items from \"{}\"."
                .format(name)
            )

        if not os.path.exists(config.path(name)):
            click.echo("List does not exist.")
            continue

        if delete:
            try:
                os.remove(config.path(name))
            except OSError:
                click.secho("Failed to delete list.", fg="red")
            else:
                click.secho("Removed file.", fg="green")
        else:
            try:
                with open(config.path(name), 'w') as fh:
                    pass
                click.secho("Cleared file.", fg="green")
            except (IOError, OSError):
                click.secho("Failed to clear list.", fg="red")

    if config.verbose:
        click.echo("Done.")


@cli.command()
@click.argument('item')
@click.argument('name', default='')
@click.option('--avoid-duplicates', is_flag=True)
@pass_config
def add(config, item, name, avoid_duplicates):
    """
    This script adds a todo item to a list.
    """
    name = name or config.default_list
    if config.verbose:
        click.echo(
            "Adding item \"{item}\" to list \"{ln}\"."
            .format(item=item, ln=name)
        )

    string = "{item}\n".format(item=item)

    if avoid_duplicates:
        try:
            if string in config.read(name):
                if config.verbose:
                    click.echo("Duplicate found.")
                return
        except TypeError:
            if config.verbose:
                click.echo("Unable to check for duplicates.")

    try:
        with open(config.path(name), 'a') as fh:
            if config.debug:
                click.secho("Opened file.", fg="cyan")
            fh.write(string)
    except (IOError, OSError):
        click.secho("Write error.", fg="red")
    else:
        if string in config.read(name, force=True):
            click.secho("Added.", fg="green")


@cli.command()
@click.argument('name')
@click.argument('items', nargs=-1)
@click.option('--avoid-duplicates', is_flag=True)
@pass_config
def adds(config, name, items, avoid_duplicates):
    if config.verbose:
        click.echo(
            "Adding to list \"{ln}\"."
            .format(ln=name)
        )

    items = ["{item}\n".format(item=item) for item in items]

    if avoid_duplicates:
        try:
            items = set(items) - set(config.read(name))
        except TypeError:
            if config.verbose:
                click.echo("Unable to check for duplicates.")

    try:
        with open(config.path(name), 'a') as fh:
            if config.debug:
                click.secho("Opened file.", fg="cyan")
            fh.writelines(items)
    except (IOError, OSError):
        click.secho("Write error.", fg="red")
    else:
        if all(item in config.read(name, force=True) for item in items):
            click.secho("Added.", fg="green")
        elif config.debug:
            click.secho("Partially added.", fg="yellow")


@cli.command()
@click.argument('item')
@click.argument('name', default='')
@click.option('--position', is_flag=True)
@pass_config
def remove(config, item, name, position):
    name = name or config.default_list
    if config.verbose:
        click.echo(
            "Removing item \"{item}\" from list \"{ln}\"."
            .format(item=item, ln=name)
        )

    if not os.path.exists(config.path(name)):
        click.echo("List does not exist.")
        return

    if position or config.default_positions:
        try:
            string = config.read(name)[int(item)]
        except ValueError:
            click.secho(
                "Item must be integer value if position is provided.",
                fg="red"
            )
            return
        except IndexError:
            click.secho(
                "Item at position \"{}\" not found."
                .format(item),
                fg="red"
            )
            return
    else:
        string = "{item}\n".format(item=item)

    if string in config.read(name):
        config.remove(name, string)
        try:
            with open(config.path(name), 'w') as fh:
                if config.debug:
                    click.secho("Opened file.", fg="cyan")
                fh.writelines(config.read(name))
        except (IOError, OSError):
            click.secho("Write error.", fg="red")
        else:
            if string not in config.read(name, force=True):
                click.secho("Removed.", fg="green")
    elif config.verbose:
        click.echo("Item not in list.")


@cli.command()
@click.argument('name', default='')
@click.argument('editor', default='/usr/bin/nano')
@pass_config
def edit(config, name, editor):
    name = name or config.default_list
    if config.verbose:
        click.echo(
            "Editing list \"{ln}\"."
            .format(ln=name)
        )

    contents = config.read(name)
    header = "# Editing list \"{0}\" - one item per line.\n".format(name)
    new_contents = click.edit(
        "{header}{items}".format(
            header=header,
            items=''.join(contents) if contents is not None else ''
        ),
        editor=editor
    )

    if new_contents is None:
        click.secho("No changes.", fg="yellow")
        return
    else:
        try:
            with open(config.path(name), 'w') as fh:
                if config.debug:
                    click.secho("Opened file.", fg="cyan")
                try:
                    fh.write(new_contents.split(header)[1])
                except IndexError:
                    pass
        except (IOError, OSError):
            click.secho("Write error.", fg="red")
        else:
            click.secho("Updated.", fg="green")


@cli.command()
@click.argument('name')
@click.argument('items', nargs=-1)
@click.option('--avoid-duplicates', is_flag=True)
@click.option('--overwrite/--no-overwrite', default=True)
@pass_config
def create(config, name, items, avoid_duplicates, overwrite):
    if config.verbose:
        click.echo(
            "Creating list \"{ln}\"."
            .format(ln=name)
        )

    if os.path.exists(config.path(name)) and not overwrite:
        click.echo("List already exists.")
        return

    items = ["{item}\n".format(item=item) for item in items]

    if avoid_duplicates:
        try:
            items = set(items)
        except TypeError:
            pass

    try:
        with open(config.path(name), 'w') as fh:
            if config.debug:
                click.secho("Opened file.", fg="cyan")
            fh.writelines(items)
    except (IOError, OSError):
        click.secho("Write error.", fg="red")
    else:
        read_items = config.read(name, force=True)
        if all(item in read_items for item in items):
            click.secho("Created list.", fg="green")
        elif config.debug:
            click.secho("Partially created list.", fg="yellow")


@cli.command()
@click.argument('name')
@click.argument('new-name')
@pass_config
def rename(config, name, new_name):
    if config.verbose:
        click.echo(
            "Renaming list \"{0}\" to \"{1}\"."
            .format(name, new_name)
        )

    try:
        os.rename(config.path(name), config.path(new_name))
    except OSError:
        click.echo("List does not exist.")
    else:
        click.echo("Renamed list.")
