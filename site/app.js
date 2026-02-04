const SONGS = [
    {
        title: "Home",
        folder: "Home",
        prefix: "Home",
        partMap: { Sop1: "Sop1", Sop2: "Sop2", Alt1: "Alt", Alt2: "Alt", Ten1: "Ten", Ten2: "Ten", Bas1: "Bas", Bas2: "Bas" }
    },
    {
        title: "It's a Republic",
        folder: "It_s a Republic",
        prefix: "ItsARepublic",
        partMap: null
    },
    {
        title: "Sure On This Shining Night",
        folder: "Sure On This Shining Night",
        prefix: "SureOnThisNight",
        partMap: null
    },
    {
        title: "The Road Home",
        folder: "The Road Home",
        prefix: "TheRoadHome",
        partMap: { Sop1: "Sop1", Sop2: "Sop2", Alt1: "Alt", Alt2: "Alt", Ten1: "Ten1", Ten2: "Ten2", Bas1: "Bas1", Bas2: "Bas2" }
    },
    {
        title: "There's Gonna Be A Homecomin'",
        folder: "There_s Gonna Be a Homecomin_",
        prefix: "TheresGonnaBe",
        partMap: { Sop1: "Sop1a", Sop2: "Sop2", Alt1: "Alt", Alt2: "Alt", Ten1: "Ten1", Ten2: "Ten2", Bas1: "Bas", Bas2: "Bas" }
    }
];

const PARTS = [
    { display: "Soprano 1", abbrev: "Sop1" },
    { display: "Soprano 2", abbrev: "Sop2" },
    { display: "Alto 1", abbrev: "Alt1" },
    { display: "Alto 2", abbrev: "Alt2" },
    { display: "Tenor 1", abbrev: "Ten1" },
    { display: "Tenor 2", abbrev: "Ten2" },
    { display: "Bass 1", abbrev: "Bas1" },
    { display: "Bass 2", abbrev: "Bas2" }
];

function getParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

function getPart() {
    return getParam("part");
}

function getPartDisplay(abbrev) {
    const part = PARTS.find(p => p.abbrev === abbrev);
    return part ? part.display : abbrev;
}

function getSong() {
    const songIndex = getParam("song");
    if (songIndex !== null && SONGS[songIndex]) {
        return SONGS[songIndex];
    }
    return null;
}

function initSongsPage() {
    const part = getPart();
    if (!part) {
        window.location.href = "index.html";
        return;
    }

    const partDisplay = document.getElementById("part-display");
    if (partDisplay) {
        partDisplay.textContent = getPartDisplay(part);
    }

    const songList = document.getElementById("song-list");
    if (songList) {
        SONGS.forEach((song, index) => {
            const link = document.createElement("a");
            link.href = `player.html?part=${part}&song=${index}`;
            link.className = "btn";
            link.textContent = song.title;
            songList.appendChild(link);
        });
    }
}

function initPlayerPage() {
    const part = getPart();
    const song = getSong();

    if (!part || !song) {
        window.location.href = "index.html";
        return;
    }

    const partDisplay = document.getElementById("part-display");
    if (partDisplay) {
        partDisplay.textContent = getPartDisplay(part);
    }

    const songDisplay = document.getElementById("song-display");
    if (songDisplay) {
        songDisplay.textContent = song.title;
    }

    const backLink = document.getElementById("back-link");
    if (backLink) {
        backLink.href = `songs.html?part=${part}`;
    }

    const audioPlayer = document.getElementById("audio-player");
    if (audioPlayer) {
        const filePart = song.partMap ? song.partMap[part] : part;
        const audioPath = `../music/${song.folder}/${song.prefix}-${filePart}Dom.mp3`;
        audioPlayer.src = audioPath;
    }
}
