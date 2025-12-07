import os

def is_dir(path):
    # Try listing contents; if it works, it's (likely) a directory
    try:
        os.listdir(path)
        return True
    except OSError:
        return False

def remove_any(path):
    # Try both remove and unlink; different ports prefer one
    try:
        os.remove(path)
        return True
    except OSError:
        try:
            os.unlink(path)
            return True
        except OSError:
            return False

def rmtree(path):
    # If it's not a directory, just remove the entry
    if not is_dir(path):
        remove_any(path)
        return

    # It's a directory: delete children first
    try:
        entries = os.listdir(path)
    except OSError:
        # Cannot list; try removing directly
        remove_any(path)
        return

    for name in entries:
        full = path + "/" + name
        if is_dir(full):
            rmtree(full)
        else:
            # File, symlink, or special node
            if not remove_any(full):
                # If removal failed because it's actually a dir, recurse
                if is_dir(full):
                    rmtree(full)

    # Finally remove the now-empty directory
    try:
        os.rmdir(path)
    except OSError:
        # Some ports allow unlink for directories; try it
        remove_any(path)

# Usage:
rmtree('/scratch')
