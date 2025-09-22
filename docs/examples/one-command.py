from acbox.cli2 import command, TypeFn, clickwrapper, Namespace


def add_arguments(fn: TypeFn) -> TypeFn:
    return fn


def process_options(options: Namespace) -> None:
    pass


@command()
@clickwrapper(add_arguments, process_options, verbose_flag=True)
def main(args: Namespace) -> None:
    "a simple script"
    pass


if __name__ == "__main__":
    main()
