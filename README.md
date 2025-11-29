# io_import_rbsp
Blender importer for Titanfall Engine map files
<!-- TODO: .gif / video guide -->


## Download

 * Get Blender:
   - [Steam](https://store.steampowered.com/app/365670/Blender/)
   - [Blender.org](https://www.blender.org/download/)
 * Get the Addon:
   - [latest release](https://github.com/snake-biscuits/io_import_rbsp/releases/)


## Installation

In **Blender** 4.5 or later:
 * `Edit > Preferences > Add-ons`
 * Click the `v` icon in the top right & select `Install from Disk`
 * Find `io_import_rbsp-X.Y.Z.zip` in the file browser
   - `X.Y.Z` is the addon version
 * Click the `Install from Disk` button


## Usage

> WARNING: Imports can take multiple minutes & consume many GB of RAM

> Test a small map before loading Olympus and setting your PC on fire


### Files to Extract
For a full import, you need:
 * `maps/mapname.bsp`
 * `models/`
 * `materials/`

You do not have to extract all the game's assets.
There will be archives with the same name as the map file.
(Except lobbies, which use the name `mp_common`)

Which archives to search:
 * Titanfall
   - `Titanfall/vpk/*mapname*_dir.vpk`
 * Titanfall 2
   - `Titanfall2/r2/pak/Win64/mapname.vpk`
   - `Titanfall2/vpk/*mapname*_dir.vpk`
 * Apex Legends
   - `ApexLegends/r2/pak/Win64/mapname.vpk`
   - `ApexLegends/r2/pak/Win64/mapname_client_perm.vpk`
   - `ApexLegends/r2/pak/Win64/mapname_client_temp.vpk`
   - `ApexLegends/vpk/*mapname*_dir.vpk` (before Season 18)

Where to extract files:
 * Extract the whole `maps/` folder to someplace you'll remember
   - for Titanfall 1 & 2 you only need the `.bsp` & `.ent` files
   - Apex Legends maps after Season 11 need `.bsp_lump` files
 * Extract `models/` & `materials/` to the same folder
   - NOTE: HarmonyVPKTool exports full paths
 * Extract `.rpak` assets w/ the extract button
   - `io_import_rbsp` will look in `exported_files/` for assets

### Extract files from `.vpk`
 * Install [HarmonyVPKTool](https://github.com/harmonytf/HarmonyVPKTool/)
 * Locate the `.vpk`s for the game you want to work with (game must be installed)
   - `Titanfall/vpk/`
   - `Titanfall2/vpk/`
   - `Apex Legends/vpk/`
 * Extract the `maps/`, `materials/` & `models/` folders
 * Some materials & models may be in `mp_common.vpk`

### Export files from `.rpak`
For this stage you will need [RSX](https://github.com/r-ex/rsx/)

Important Settings:
 * Export asset names, not GUIDs
 * Full asset paths
 * Material as .json (Raw Struct)
 * Texture as .dds (All Mips)

Extract all `_wld` & `_fix` materials.
Textures linked to materials should be exported automatically.

Apex Legends `.rpak` should also include `maps/` & `models/`

### Import Map
Warnings:
 * This can use a lot of RAM (16GB+ for a Titanfall 2 map)
 * Seriously pushes Blender to it's limits
   - Vulkan backend + AMD GPU + Linux = crash; **use OpenGL**
 * Save work & close other programs before loading
 * Test with a small map first to see how your PC fares

Once you've extracted the files you need:
 * Set `Properties > Scene > Titanfall Engine Assets` folders
   - `RSX Folder` should contain `rsx.exe` & `exported_files/`
   - `VPK Folder` should contain `models/` & `materials/`
 * `File > Import > Titanfall Engine .bsp`
 * Select the `.bsp` (`.bsp_lump` & `.ent` files need to be in the same folder)
 * Choose your settings
 * Click Import
 * Wait a few minutes (Can easily take 1hr+ on Apex Legends maps)


## Other Tools

### Respawn VPK
 * [HarmonyVPKTool](https://github.com/harmonytf/HarmonyVPKTool/releases/latest)

### Porting Tools
 * [VRChat-Titanfall-Unity-Tools](https://github.com/Swagguy47/VRChat-Titanfall-Unity-Tools)

### More Blender Addons
 * [`SourceIO`](https://github.com/REDxEYE/SourceIO)
   - GoldSrc & Source Engine importer (`.bsp`, `.vmt`, `.vtf`, `.mdl`)
 * [`SourceOps`](https://github.com/bonjorno7/SourceOps)
   - Source Engine model exporter
 * [`PyD3DBSP`](https://github.com/mauserzjeh/PyD3DBSP) (Archived)
   - Call of Duty 2 `.bsp` importer
 * [`blender_io_mesh_bsp`](https://github.com/andyp123/blender_io_mesh_bsp)
   - Quake 1 `.bsp` importer
 * [`Blender_BSP_Importer`](https://github.com/QuakeTools/Blender_BSP_Importer)
   - Quake 3 `.bsp` importer


## Modding Community Links
  * Titanfall 1:
    - [Harmony](https://harmony.tf/)
  * Titanfall 2:
    - [Northstar](https://northstar.tf/)
    - [Titanfall 2 Speedrunning](https://www.speedrun.com/titanfall_2)
  * Apex Legends:
    - [Legion+](https://github.com/r-ex/LegionPlus)
    - [R5Reloaded](https://r5reloaded.com/)
<!-- TODO: add Titanfall Online Revive when they go public -->
