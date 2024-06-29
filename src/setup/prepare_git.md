# Prepare Git

Since we are collaborating on Git-base platforms, the first setup before committing your code is to prepare your git and git-related presets.

## Signature

To provide information on authors and contacts of specific commit, the commit should be committed with `-s` option (which dicates git to leave a git signature at the bottom of commit message). But before `-s` could function properly, you will need to tell git about your basic information with command:

```bash
$ git config --global user.name "<name>"
$ git config --global user.email "<email>"
```

## Sign Commit

### Generate GPG Key

It would be better if your commit is signed with your GPG key. If you don't have a GPG key yet, you can generate one with:

```bash
$ gpg --full-generate-key
```

after you complete the settings about the newly generated GPG key, retrieve the `keyid` with command:

```bash
$ gpg --list-secret-keys --keyid-format=long
```

This would give you a output like below:

```bash
$ gpg --list-secret-keys --keyid-format=long
/Users/hubot/.gnupg/secring.gpg
------------------------------------
sec   4096R/3AA5C34371567BD2 2016-03-10 [expires: 2017-03-10]
uid                          Hubot <hubot@example.com>
ssb   4096R/4BB6D45482678BE3 2016-03-10
```

and the partern after `/` in `sec` column (in this case `3AA5C34371567BD2`) is the `keyid` of the GPG key you just generated.

To Add it into your Github GPG keys, you will need to export it with command:

```bash
$ gpg --armor --export 3AA5C34371567BD2
# Prints the GPG key ID, in ASCII armor format
```

### Update Github

The content printed by `gpg --armor --export <GPG Key ID>` is the `GPG PUBLIC KEY BLOCK` to be pasted in your Github accout's GPG key section.

### Update Git Config

To make the `-S` option work, Git has to know about the `keyid` to be signed with, this could be set with command:

```bash
$ git config --global user.signingkey "<GPG Key ID>"
```

### Set GPG TTY

GPG TTY should be set properly for `gpg-agent` to work, it could be done by adding the following lines to your `.bashrc`, scripts under `profile.d` or whatever make it apply:

```bash
# This is for bash
export GPG_TTY=$(tty)
```

After all these steps are observed, you are now able to sign your commit with option `-s` (leaves a Git signature) and `-S` (sign commit with a GPG key). You generally need to commit with command:

```bash
$ git commit -s -S
```

