# Blueprints - FreeCAD Addon for rapid sketching

Quickly insert complex sketches with a single click – variables & expressions included.
Reduce repetetive work by loading pre-defined sketches.

For example, add a USB-C port (hole) to your electronics case in seconds:

<video width="100%" style="max-width: 1024px" src="doc/basic-insert.mp4" controls></video>

https://github.com/user-attachments/assets/05db9d5e-0224-46a2-8365-9c46397f8b67


## Features

**Define your own sketches** with tools you are already familiar with: FreeCAD.
Blueprints are sketches loaded from another FreeCAD file.
You can fully constraint your sketch relative to the axis origin (e.g., distance to PCB).
All constraints and expressions are copied to the new destination.

If a blueprint contains only one sketch, it is loaded right away.
If the file contains multiple sketches, a popup will ask you which sketch to load (second window in the video above).


## Example Usage

See also [Creators Guide](doc/README-Creators.md).


### Insert multiple copies

<video width="100%" style="max-width: 1024px" src="doc/multi-insert.mp4" controls></video>

https://github.com/user-attachments/assets/e0067a6b-6e72-4161-9450-a4a240367cbf


### Create new blueprint from selection

<video width="100%" style="max-width: 1024px" src="doc/create-from-selection.mp4" controls></video>

https://github.com/user-attachments/assets/493449f3-9845-4fc3-ae09-eef69309767e


### Co-dependent copies

<video width="100%" style="max-width: 1024px" src="doc/named-equals.mp4" controls></video>

https://github.com/user-attachments/assets/8e3b9420-0521-4c40-9158-be71a763becb

## Roadmap

- [ ] Translations
- [ ] Community managed content (subscribe to other users blueprints, e.g. git repo)
