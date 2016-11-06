# languages4iOS

## What it is

When you're working on a project with several languages, updating and adding to all your language files can be a huge pain.
languages4iOS is a python script I wrote to help manage all the language files on an iOS project.
It creates a correspondance between all your "Localizable" files and a single and more manageable languages.csv file.

## Usage 
```
python languages.py export
```
will search for your language files in your iOS project and create a single and more manageable languages.csv file for you to update your translations.

```
python languages.py import
```
will search for a languages.csv file and use it to create all the relevant language files.

```
python languages.py update
```
will update your language files according to the changes in the languages.csv file.
