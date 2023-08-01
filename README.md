# io_import_rbsp
Blender 2.93 importer for `rBSP` files (Titanfall Engine `.bsp`)


<!-- TODO: .gifs for guides -->
## Installation
 * Get Blender 2.93+ from [Steam](https://store.steampowered.com/app/365670/Blender/) / [Blender.org](https://www.blender.org/download/)
 * Head over to [releases](https://github.com/snake-biscuits/io_import_rbsp/releases/) & download `io_import_rbsp_v1.2.0_b2.93.zip`  
Then, in Blender:  
 * `Edit > Preferences > Add-ons > Install`
 * Find `io_import_rbsp_v1.2.0_b2.93.zip`
 * Click `Install Addon`
 * Check the box to enable `Import-Export: io_import_rbsp`


## Usage

> WARNING: Titanfall Engine maps are huge  
> Imports can take multiple minutes and a few GB of RAM for the geometry alone  
> Test a small map before loading Olympus and setting your PC on fire

### Extracting `.bsp`s
You will need to extract `.bsp`, `.bsp_lump` & `.ent` files for any map you want to extract. To do this:
 * Grab a [Respawn VPK extractor](#Respawn-VPK)
 * Locate the `.vpk`s for the game you want to work with (game must be installed)
   - `Titanfall/vpk/`
   - `Titanfall2/vpk/`
   - `Apex Legends/vpk/`
 * Open the `*.bsp.pak000_dir.vpk` for the map you want to load
   - Titanfall 2 map names can be found here: [NoSkill Modding Wiki](https://noskill.gitbook.io/titanfall2/documentation/file-location/vpk-file-names)
   - Lobbies are stored in `mp_common.bsp.pak000_dir.vpk`
 * Extract the `.bsp`, `.ent`s & `.bsp_lumps` from the `maps/` folder to someplace you'll remember
   - each `.vpk` holds assets for one `.bsp` (textures and models are stored elsewhere)
<!-- TODO: Materials & Models -->

### Blender Importer
Once you've extracted the files you need:
 * `File > Import > Titanfall Engine .bsp`
 * Select the `.bsp` (`.bsp_lump` & `.ent` files need to be in the same folder)
 * Choose your settings
 * Click Import
 * Wait a few minutes (Can easily take 1hr+ on Apex Legends maps)
<!-- Cry when it breaks and send me an e-mail to fix it -->
<!-- Materials & Models will require paths set in Preferences & SourceIO -->

### Legion Assets
**TITANFALL 2 & APEX LEGENDS ONLY! (EXPERIMENTAL)**
- Titanfall: `.vpk` Materials & Models
- Titanfall 2: `.rpak` Materials; `.vpk` Models
- Apex: `.rpak` Materials & Models
 * [Legion Workflow](https://drive.google.com/file/d/1ApByE0p5MzVV95dUsQ0seciCA7Cl5WFZ/view)
 * Requires:
   - [.cast](https://github.com/dtzxporter/cast)
   - [.mprt](https://github.com/llennoco22/Apex-mprt-importer-for-Blender)



## Related Tools

### Respawn VPK
 * [Titanfall_VPKTool3.4_Portable](https://github.com/Wanty5883/Titanfall2/blob/master/tools/Titanfall_VPKTool3.4_Portable.zip) (GUI only)
   - by `Cra0kalo` (currently Closed Source) **recommended**
 * [TitanfallVPKTool](https://github.com/p0358/TitanfallVPKTool) (GUI & CLI)
   - by `P0358`
 * [RSPNVPK](https://github.com/squidgyberries/RSPNVPK) (CLI only)
   - Fork of `MrSteyk`'s Tool
 * [UnoVPKTool](https://github.com/Unordinal/UnoVPKTool) (CLI only)
   - by `Unordinal`

### Other
 * [SourceIO](https://github.com/REDxEYE/SourceIO)
   - GoldSrc & Source Engine importer (`.bsp`, `.vmt`, `.vtf`, `.mdl`)
 * [SourceOps](https://github.com/bonjorno7/SourceOps)
   - Source Engine model exporter
 * [Perimeter](https://github.com/EM4Volts/Perimeter)
   - Titanfall 2 `.mdl` editing QoL tool
 * [PyD3DBSP](https://github.com/mauserzjeh/PyD3DBSP) (Archived)
   - Call of Duty 2 `.bsp` importer
 * [blender_io_mesh_bsp](https://github.com/andyp123/blender_io_mesh_bsp)
   - Quake 1 `.bsp` importer
 * [Blender_BSP_Importer](https://github.com/QuakeTools/Blender_BSP_Importer)
   - Quake 3 `.bsp` importer

## FAQs
 * No Textures / Models?
   - I'm working on it
 * Why can't I see anything?
   - Titanfall Engine maps are huge, you need to increase your view distance
   - `3D View > N > View > Clip Start: 16, End: 102400` (only affects that 3D view)
     - You will also need to increase the clipping distance for all cameras
 * Why is my `.blend` file still huge after I deleted everything?
   - Blender keeps deleted items cached in case you want to undo
   - To clear this cache use: `File > Clean Up > Recursive Unused Data Blocks`
   - Or set the **Outliner** display mode to **Orphan Data** & click **Purge**
 * It broke? Help?
   - Ask around on Discord, you might've missed a step someplace
   - If you're loading a brand new Apex map, it might not be supported yet
 * Can I use this to make custom maps?
   - No, we don't know enough about Respawn's `.bsp` format to make compilers
   - As easy as it might sound on paper, editing a `.bsp` directly is no small task
 * Can I use this for animations?
   - Sure! but be sure to credit the tool someplace
   - And credit Respawn too! they made the maps in the first place

### Further Questions

> NOTE: I am a full-time Uni Student in an Australian Timezone  
> Don't go expecting an immediate response

Open a GitHub Issue with the `question` label  
If you don't want a GitHub account I can be found on Discord as `b!scuit#3659`  
**Send your Question in a Message Request or I'll assume you're a bot**

You can also find me in these Titanfall & Apex Discords:
  * Titanfall 1:
    - Harmony
  * Titanfall 2:
    - Northstar
    - Titanfall 2 Speedrunning
  * Apex Legends:
    - Legion+
    - R5Reloaded
<!-- TODO: add Titanfall Online Revive when they go public -->

**If you join one of the above Discords just to add me, I'll assume you're a bot**
