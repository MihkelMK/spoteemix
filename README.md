# spoteemix

Previously I used the Spotify integration inside Deemix, but it has stopped working.

Took it into my hands and created a Python script to get the song data using Spotify APIs and then search for songs in Deemix using that data.

## Prerequisites

Go to your [Spotify developer dashboard](https://developer.spotify.com/dashboard) and create a project.\
Save the client_id and client_secrets to either environment variables `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` or into `~/.config/spoteemix/config.json`.

### Example `config.json`

```json
{
  "client_id": "xxxx",
  "client_secret": "xxxx",
  "deemix": "http://ip:port/"
}
```

## Install

Replace x.x with the current version number in file names.

### Create build

After cloning this repo, create a new build with (you might need to `pip install build`)

```sh
python3 -m build
```

This creates a file called `spoteemix-x.x.tar.gz` into `dist`.\

### Install build

The next steps depend on your OS.

### Windows

```sh
python3 -m pip install ./dist/spoteemix-x.x.tar.gz
```

### Linux

**If you have externally managed environments, like on Arch, look at the next paragraph**

```sh
pip3 install ./dist/spoteemix-x.x.tar.gz
```

### Linux w/ External Management

There are 2 options.

- Make a project specific virtual environment and run the command above.
- Use [pipx](https://pipx.pypa.io/).

For ease of use, we'll go with `pipx`. It installs and runs packages in isolated environments while still making them globally available.

Install `spoteemix` with `pipx`:

```sh
pipx install ./dist/spoteemix-x.x.tar.gz
```

`pipx` will now warn you that `~/.local/bin` is not in `$PATH`.\
This means `spoteemix` won't be globally available. To fix this, run:

```sh
pipx ensurepath
```

`pipx` will now add `~/.local/bin` to path and `spoteemix` will be available for any new shell instances.
