# Elite Explorer

The project's goal is to help find (nearby) systems that are
- not yet known to [EDSM](https://www.edsm.net/) or [Spansh](https://www.spansh.co.uk/) or
- are logged to [Spansh](https://www.spansh.co.uk/), but not fully explored.

Currently only works with the stand alone version, as [EDMC-Plugin](https://github.com/PierFelix/elite_explorer_edmc/tree/EDMC-Plugin) still needs more development. 

### Requirements
See the list of python dependencies in [requirements.txt](./requirements.txt).  
Requires python 3, tested on version 3.14.9.

### Usage
- Check if the journal directory inside [main.py](./main.py) is set correctly:  
` journal_dir = os.path.expanduser(r"<path_to_your_journal_directory>")`
- Run [main.py](./main.py), the program will detect the latest journal and if this is not an old journal.
- Either load fully into the game, or jump into a new system if the game was already running.
- A list of the closest systems in a 20 LY range is requested from [EDSM](https://www.edsm.net/)
  - if `SHOW_PARTIALLY_EXPLORED` is set to `True`, all systems are also checked with [Spansh](https://www.spansh.co.uk/)
- Target a system using the navigation panel to check if the system is "known" (was sent by [EDSM](https://www.edsm.net/))
  - if the system was not in the list, a message will appear that `<system_name> is not known by EDSM!`
- To list all fully unknown systems (according to [EDSM](https://www.edsm.net/)), open the `Galnet News` or `Powerplay` panel.
  - this will print out `Fully Unexplored Systems:` followed by the unexplored systems.
  - if the list is empty, no systems will follow. Either
    - no unexplored systems are in a 20 LY radius or
    - the systems were not checked by individually targeting them in the navigation panel
- To list both fully unknown ([EDSM](https://www.edsm.net/)) and partially explored ([Spansh](https://www.spansh.co.uk/)) systems, open the `Codex` panel.
  - This prints `Fully Unexplored Systems:` like before and is followed by a `Partially Explored Systems:`.
    - if the second list is empty this can be due to no partially explored systems present or `SHOW_PARTIALLY_EXPLORED` is set to `False`

### Limitations
- We cannot select the systems automatically, they only appear in the journal files once targeted...
- The list of unknown systems will not be trimmed, unless `CLEAR_UNKNOWNS` is set to `True` (will delete all entries after jump). (https://github.com/PierFelix/elite_explorer_edmc/issues/7)
- Some HTTP error codes are not yet handled correctly (https://github.com/PierFelix/elite_explorer_edmc/issues/3 & https://github.com/PierFelix/elite_explorer_edmc/issues/6)
- Likely plenty more that I cannot think of right now

### Description from original code:
> # Elite Explorer
> The goal of this is to make finding unexplored systems faster and easier with the help of EDSM.
>
> When loading or entering a new system, we do the following
> - Collect the surrounding systems in a 20ly radius
> - Order them by distance
> - Print that list including the currently known bodies in the system
> - Any system with no bodies discovered has potential first discoveries
> - Any system not in the EDSM list but in the nearby systems target list is also potentially undiscovered.
>
> It seems to be pretty effective at the moment, and improvements to UI and general logic are appreciated.

