#!/bin/bash

set -u

if [[ "$PWD" != "$(cd "$(dirname "$0")" && pwd)" ]]; then
  echo "The script must be run from within its directory."
  exit 1
fi

TARGET="$HOME/.config/sublime-text"

# editorconfig
rm -f "$TARGET/.editorconfig"
ln -s "$PWD/.editorconfig" "$TARGET/.editorconfig"

# builds
for BUILD in "exec_only_failed_output_build.py"; do
  rm -f "$TARGET/Packages/User/$BUILD"
  ln -s "$PWD/build/$BUILD" "$TARGET/Packages/User/$BUILD"
done

# plugins
for PLUGIN in "MarkdownToHtml" \
  "OpenUrlPanel" \
  "RunCommand" \
  "RunOnEvent" \
  "SwitchPanel"; do
  rm -f "$TARGET/Packages/$PLUGIN"
  ln -s "$PWD/plugins/$PLUGIN" "$TARGET/Packages/$PLUGIN"
done

# settings
for SETTING in "CSS.sublime-settings" \
  "Default (Linux).sublime-keymap" \
  "Default.sublime-commands" \
  "Dracula Neue Pro (Alucard).sublime-color-scheme" \
  "easy_diff.sublime-settings" \
  "HTML.sublime-settings" \
  "LSP-gopls.sublime-settings" \
  "LSP-jdtls.sublime-settings" \
  "LSP.sublime-settings" \
  "PackageDev.sublime-settings" \
  "PackageResourceViewer.sublime-settings" \
  "Package Control.sublime-settings" \
  "Preferences.sublime-settings" \
  "Sublime Text Color Scheme.sublime-settings" \
  "Sublime Text Commands.sublime-settings" \
  "Sublime Text Keymap.sublime-settings" \
  "Sublime Text Menu.sublime-settings" \
  "Sublime Text Mousemap.sublime-settings" \
  "Sublime Text Settings.sublime-settings" \
  "Sublime Text Theme.sublime-settings" \
  "Terminus.sublime-settings" \
  "mdpopups.css"; do
  rm -f "$TARGET/Packages/User/$SETTING"
  ln -s "$PWD/settings/$SETTING" "$TARGET/Packages/User/$SETTING"
done

# language syntaxes
for SYNTAX in "Gettext.tmLanguage" \
  "Jinja.sublime-syntax" \
  "Just.sublime-syntax" \
  "Meson.tmLanguage"; do
  rm -f "$TARGET/Packages/User/$SYNTAX"
  ln -s "$PWD/syntax/$SYNTAX" "$TARGET/Packages/User/$SYNTAX"
done
