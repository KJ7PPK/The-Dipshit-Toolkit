I'll keep an overview of the different tools and scripts here as time permits. Various stuff I've had to make in the administration of my Debian, Ubuntu, and Windows workstations and servers.

**Python Stuff**
MediaIntegrityChecker
Totally clanker-created, to check a specified directory's media files (covers most video and photo formats), detect corrupt files and move them into a child directory, and report how many were corrupt vs. valid. I needed this to check randomly named files that were recovered via PhotoRec from a HDD that had a file system go bonkers.

ImportAlbumsToLidarr
From a CSV (generated mine with exportify, connect to Lidarr via API and attempt to add all artists and/or albums to the database. Prompts user for URL, API, console options, log file options, etc.
