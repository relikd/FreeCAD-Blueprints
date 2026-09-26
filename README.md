# Blueprints - FreeCAD Addon for rapid sketching

Reduce repetetive work by loading pre-defined sketches from community collections.

For example, add a USB-C port (hole) to your electronics case in seconds. 

[TODO: add usage animation]


### About this project

> [!IMPORTANT]
> This addon is still in development.
> The basic functionaly it there, but it still needs lots of usability tweaking.


### Roadmap

- [ ] Documentation
	- instructions on how to create blueprints
	- documentation / description for the addon store
	- proper dev documentation (this Readme++)
- [ ] Improve blueprint insert workflow
	- cursor icon for blueprint placement
	- where to show "allow rotation" option/checkbox?
	- check if there are other expressions than in-sketch refs
	- thumbnail preview of the sketch prior to import
- [ ] Allow user to (easily) create new blueprints
	- shortcut to create new document in user-collection
	- create empty sketch via `Part` (avoids a body object)
	- usage instructions (`desc` property, fully constrain to origin, ...)
- [ ] Preferences page
	- manage location of user-collection
	- manage subscriptions (with update button?, we need versions)
- [ ] Allow bp-creators to define variables?
	- either by Sketch properties or via `VarSet`
	- how are multiple instances handled?
- [ ] General improvements
	- Qt string translations
- [ ] Community managed content
	- add mechanism to subscribe to community managed blueprints
	- either via git (not installed everywhere) or bundled with addon (less updates)
	- At the very least, have a markdown with links to great sources
