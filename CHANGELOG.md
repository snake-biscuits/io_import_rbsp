# Changelog

## v1.2.2_b2.93 (8th December 2021)

### Updates
 * Models & Textures via [Legion](https://wiki.modme.co/wiki/apps/Legion.html) **(experimental)**; requires:
   - [.cast](https://github.com/dtzxporter/cast)
   - [.mprt](https://github.com/llennoco22/Apex-mprt-importer-for-Blender)

> Faster methods (as part of io_import_rbsp) are planned, this was just easier to implement


## v1.2.1_b2.93 (8th December 2021)

### Updates
 * Updated internal `bsp_tool` to [latest version](https://github.com/snake-biscuits/bsp_tool/commit/13836462855b4cbd8049098a1df350b71eb1094f)

### Fixed
 * Apex Legends Season 11 (post 19th November path) maps are now correctly detected


## v1.2.0_b2.93 (1st October 2021)

### Added
 * Entity naming resolution order is now `targetname -> editorclass -> classname`
 * All brush entities now generate geo and are coloured from a hard-coded palette

### Fixed
 * Generated trigger brush geo is no longer inside-out


## v1.1.0_b2.93 (1st October 2021)

### Added
 * Geometry for `trigger_*` brush entities is now generated on import


## v1.0.0_b2.93 (28th September 2021)
Initial Release
