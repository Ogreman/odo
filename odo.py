import os
import click


class Config(object):

    def __init__(self):
        self.verbose = False
        self.debug = False
        self.list_dir = ""
        self._paths = {}
        self._lists = {}

    def path(self, list_name=None):
        if list_name is not None:
            if list_name in self._paths:
                if self.debug:
                    click.echo(
                        "Using path cache for \"{}\"."
                        .format(list_name)
                    )
                path = self._paths[list_name]
            else:
                if self.debug:
                    click.echo(
                        "Setting path cache for \"{}\"."
                        .format(list_name)
                    )
                path = os.path.expanduser(
                    "{dir}{sl}.{name}.odo"
                    .format(
                        dir=self.list_dir,
                        name=list_name,
                        sl="" if self.list_dir.endswith('/') else "/",
                    )
                )
                self._paths[list_name] = path
            return path
        else:
            return os.path.expanduser(self.list_dir)

    def find_lists(self):
        try:
            list_names = [
                file_name[1:-len('.odo')]
                for file_name in os.listdir(self.path())
                if file_name.endswith('.odo')
            ]
            for name in list_names:
                if self.debug:
                    click.echo(
                        "Setting path cache for \"{}\"."
                        .format(name)
                    )
                self._paths[name] = os.path.expanduser(
                    "{dir}{sl}.{name}.odo"
                    .format(
                        dir=self.list_dir,
                        name=name,
                        sl="" if self.list_dir.endswith('/') else "/",
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
                        click.echo("Opened file.")
                    self._lists[list_name] = fh.readlines()
                    if self.debug:
                        click.echo(
                            "Set list cache for \"{}\"."
                            .format(list_name)
                        )
            except (IOError, OSError):
                if self.verbose:
                    click.echo("Failed to read list.")
                return None
        elif self.debug:
            click.echo(
                "Using list cache for \"{}\"."
                .format(list_name)
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


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--verbose', is_flag=True)
@click.option('--debug', is_flag=True)
@click.option('--list-dir', default='~/', help="This is the directory of lists.")
@pass_config
def cli(config, verbose, debug, list_dir):
    config.verbose = verbose
    config.debug = debug
    config.list_dir = list_dir


@cli.command()
@click.argument('name', default='default')
@pass_config
def list(config, name):
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
        for item in items:
            click.echo(">> {0}".format(item.rstrip()))
        if config.verbose:
            click.echo("Done.")


@cli.command()
@click.option('--lol', is_flag=True)
@pass_config
def lists(config, lol):
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
                    name=name,
                    count=count
                )
            )
            if lol:
                if config.verbose:
                    click.echo(
                        "Listing items from \"{ln}\"."
                        .format(ln=name)
                    )
                for item in config.read(name):
                    click.echo(">> {0}".format(item.rstrip()))
        if config.verbose:
            click.echo("Done.")


@cli.command()
@click.argument('name', default='default')
@click.option('--delete', is_flag=True)
@pass_config
def clear(config, name, delete):
    if config.verbose:
        click.echo(
            "Clearing items from \"{}\"."
            .format(name)
        )

    if not os.path.exists(config.path(name)):
        click.echo("List does not exist.")
        return

    if delete:
        try:
            os.remove(config.path(name))
        except OSError:
            click.echo("Failed to delete list.")
        else:
            click.echo("Removed file.")
    else:
        try:
            with open(config.path(name), 'w') as fh:
                pass
            click.echo("Cleared file.")
        except (IOError, OSError):
            click.echo("Failed to clear list.")
    if config.verbose:
        click.echo("Done.")



@cli.command()
@click.argument('item')
@click.argument('name', default='default')
@click.option('--avoid-duplicates', is_flag=True)
@pass_config
def add(config, item, name, avoid_duplicates):
    """
    This script adds a todo item to a list.
    """
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
            pass

    try:
        with open(config.path(name), 'a') as fh:
            if config.debug:
                click.echo("Opened file.")
            fh.write(string)
    except (IOError, OSError):
        click.echo("Write error.")
    else:
        if string in config.read(name, force=True):
            click.echo("Added.")


@cli.command()
@click.argument('item')
@click.argument('name', default='default')
@pass_config
def remove(config, item, name):
    if config.verbose:
        click.echo(
            "Removing item \"{item}\" from list \"{ln}\"."
            .format(item=item, ln=name)
        )

    string = "{item}\n".format(item=item)
    if string in config.read(name):
        config.remove(name, string)
        try:
            with open(config.path(name), 'w') as fh:
                if config.debug:
                    click.echo("Opened file.")
                fh.writelines(config.read(name))
        except (IOError, OSError):
            click.echo("Write error.")
        else:
            if string not in config.read(name, force=True):
                click.echo("Removed.")
    elif config.verbose:
        click.echo("Item not in list.")
