// state variables
let currentFormatFilter = ""
let currentGenreFilter = "" // "" means all

// --- Spotify OAuth Handling ---
window.addEventListener("DOMContentLoaded", async () => {
    const url = new URL(window.location.href);
    // Detect server redirect after successful Spotify connect
    if (url.searchParams.get('spotify_connected') === '1' || url.searchParams.get('spotify_connected') === 'true') {
        // mark connected and remove the param
        localStorage.setItem("spotify_connected", "1");
        url.searchParams.delete('spotify_connected');
        window.history.replaceState({}, document.title, url.toString());
        // reload main page state (will call displayUserCollection etc.)
        const sessionID = localStorage.getItem('sessionID');
        if (sessionID) {
            await loadMainPage();
        } else {
            showLoginPage();
        }
        return;
    }

    // Normal app load: if user already connected, load main page; otherwise show login
    const sessionID = localStorage.getItem('sessionID');
    if (sessionID && localStorage.getItem("spotify_connected") === "1") {
        await loadMainPage();
    } else if (sessionID) {
        // Has session but not Spotify connected
        await loadMainPage();
    } else {
        // No session at all
        showLoginPage();
    }
});

function showLoginPage() {
    document.querySelector("#login-container").style.display = "block";
    document.getElementById("main-app").style.display = "none";
}

async function loadMainPage() {
    document.querySelector("#login-container").style.display = "none";
    document.getElementById("main-app").style.display = "block";

    await displayUserCollection();
    await displayUserWishlist();
}

// init page
// ---add genre dropdown options based on user database---
async function initDropdown(entry) {
    let genreDropdown = document.querySelector("#genre-dropdown")
    let genres = entry.genre.split(",").map(g => g.trim()).filter(g => g)
    
    genres.forEach(genre => {
        if (![...genreDropdown.options].some(opt => opt.value === genre)){
            let option = document.createElement("option")
            option.value = genre
            option.innerHTML = genre
            genreDropdown.appendChild(option)
        }
    })
}

// display all user's saved records
async function displayUserCollection(){
    console.log("displaying user collection")
    document.getElementById("collection-section").style.display = "flex"
    const response = await fetch("http://localhost:8080/vinyl", {
        headers:{
            "Authorization": authorizationHeader()
        }
    })
    const data = await response.json()
    console.log(data)
    for (const entry of data){
        buildRelease(entry.artist, entry.album, entry.cover_image, entry.url, "collection", entry.format, entry.genre)
        initDropdown(entry)
    }
}

async function displayUserWishlist(){
    console.log("displaying user collection")
    const response = await fetch("http://localhost:8080/wishlist", {
        headers:{
            "Authorization": authorizationHeader()
        }
    })
    const data = await response.json()
    console.log(data)
    for (const entry of data){
        buildRelease(entry.artist, entry.album, entry.cover_image, entry.url, "wishlist", entry.format, entry.genre)
    }
}

// ---------------------------------------------------------------------------------------------------
// submit

//let token = 
/*
let resourceURL = ""
let artistName = '' 
let albumName = ''
let releaseBarcode = ''
let coverImageUrl = ''
*/

function submitBarcode(collectionOrWishlist){
    let barcode = document.querySelector("#barcode-input").value.replaceAll(' ', '')
    document.querySelector("#barcode-input").value = ""

    let existingRecord = document.getElementById(barcode.replaceAll(' ', ''))
    if (existingRecord != null){
        if (confirm("You already have this barcode recorded, record again?")) {
            fetchBarcode(barcode, "barcode", collectionOrWishlist)
        }
    } else {
        fetchBarcode(barcode, "barcode", collectionOrWishlist)
    }
}

function submitAlbumArtist(collectionOrWishlist){
    let artistInput = document.querySelector("#artist-input").value
    let albumInput = document.querySelector("#album-input").value

    if (!albumInput && !artistInput) {
        alert("Please enter an ablum name or artist name")
        return
    }

    document.querySelector("#album-input").value = ''
    document.querySelector("#artist-input").value = ''

    let query = ""
    if (artistInput && albumInput) {
        query = `${artistInput} ${albumInput}`
    } else if (artistInput) {
        query = artistInput
    } else {
        query = albumInput
    }

    // Call fetchBarcode with "q" for general search
    fetchBarcode(query, "q", collectionOrWishlist)

    /*let title = albumInput + '&artist=' + artistInput

    console.log(title)
    */

    //fetchBarcode({release_title: albumInput, artist: artistInput}, "release_title", collectionOrWishlist)
}

function submitSearch(collectionOrWishlist){
    let searchInput = document.querySelector("#search-input").value
    document.querySelector("#search-input").value = ''

    fetchBarcode(searchInput, "q", collectionOrWishlist)
}

function postRecord(resourceURL, albumName, artistName, coverImageUrl, genre, format){
    fetch('http://localhost:8080/vinyl', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': authorizationHeader()
        },
        body: `url=${encodeURIComponent(resourceURL)}&album=${encodeURIComponent(albumName)}&artist=${encodeURIComponent(artistName)}&cover_image=${encodeURIComponent(coverImageUrl)}&genre=${encodeURIComponent(genre)}&format=${encodeURIComponent(format)}`
    })
    .then(response => {
        if (response.status === 201){
            clearSections()
            navCollection()
        } else if (response.status === 401){
            alert("Session expired. Please log in again.")
        } else {
            alert("Error: Could not save record. Please try again")
            console.error("Response status:", response.status)
        }
    })
    .catch(() => {
        alert("Network error: Could not connect to server.")
        console.error("Fetch error:", error)
    })
}

function postWishlist(resourceURL, albumName, artistName, coverImageUrl, genre, format){
    fetch('http://localhost:8080/wishlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': authorizationHeader()
        },
        body: `url=${encodeURIComponent(resourceURL)}&album=${encodeURIComponent(albumName)}&artist=${encodeURIComponent(artistName)}&cover_image=${encodeURIComponent(coverImageUrl)}&genre=${encodeURIComponent(genre)}&format=${encodeURIComponent(format)}`
    })
    .then(response => {
        if (response.status === 201){
            clearSections()
            navWishlist()
        } else {
            alert("Error: Could not save record. Please try again")
        }
    })
    .catch(() => {
        alert("Network error: Could not connect to server.")
    })
}


function fetchBarcode(barcode, search_type, section){
    let collection = document.querySelector("#" + section + "-div")

    let query = ""
    if (typeof barcode === "object") {
        query = Object.entries(barcode)
            .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
            .join("&")
    } else {
        query = barcode
    }
    return fetch(`http://localhost:8080/api/discogs/search?query=${encodeURIComponent(query)}&type=${encodeURIComponent(search_type)}`, {
        headers: {
            'Authorization': authorizationHeader()
        }
    })
        // add type to search 
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                return new Promise((resolve) => {
                    // confirm correct album -- results popup
                    let resultsPopup = document.createElement("div")
                    resultsPopup.className = "results-popup"
                    data.results.forEach((result, idx) => {
                        let resultDiv = document.createElement("div")
                        resultDiv.className = "result-div"
                        let leftCol = document.createElement("div")
                        leftCol.className = "left-col"

                        // Album info
                        let link = document.createElement("a")
                        let title = document.createElement("h2")
                        let artist = document.createElement("p")
                        let cover = document.createElement("img")

                        link.target = "_blank"
                        link.href = "https://www.discogs.com" + result.uri
                        
                        const titleParts = result.title.split(" - ")
                        artistName = titleParts[0]
                        albumName = titleParts[1]
                        coverImageUrl = result.cover_image

                        title.innerHTML = albumName || result.title
                        artist.innerHTML = artistName || ""
                        cover.src = result.cover_image

                        link.appendChild(title)
                        leftCol.appendChild(cover)
                        leftCol.appendChild(link)
                        leftCol.appendChild(artist)

                        // format
                        let formatP = document.createElement("p")
                        formatP.innerHTML = "Format: "

                        if (result.formats) {
                            formatP.innerHTML += result.formats[0].name + " - "
                            result.formats[0].descriptions?.forEach(description => {
                                formatP.innerHTML += description + " - "
                            })
                            if (result.formats[0].text) {
                                formatP.innerHTML += result.formats[0].text
                            }
                        } else if (result.format) {
                            result.format?.forEach(description => {
                                formatP.innerHTML += description + " - "
                            })
                        }

                        formatP.innerHTML = formatP.innerHTML.replace(/ - $/, '')

                        leftCol.appendChild(formatP)
                        resultDiv.appendChild(leftCol)

                        // select button
                        let rightCol = document.createElement("div")
                        rightCol.className = "right-col"
                        let selectBtn = document.createElement("button")
                        selectBtn.innerHTML = "Select"
                        selectBtn.onclick = function () {
                            handleResultSelection(idx)
                        }

                        rightCol.appendChild(selectBtn)
                        resultDiv.appendChild(rightCol)

                        resultsPopup.appendChild(resultDiv)
                    })

                    let overlay = document.getElementById("overlay")
                    overlay.appendChild(resultsPopup)
                    overlay.style.display = "block"

                    async function handleResultSelection(selectedIdx) {
                        const release = data.results[selectedIdx]

                        console.log(release)

                        const titleParts = release.title.split(" - ")
                        let artistName = titleParts[0]
                        let albumName = titleParts[1]
                        let coverImageUrl = release.cover_image
                        let resourceURL = release.resource_url
                        let genre = release.genre
                        let genreString = Array.isArray(genre) ? genre.join(",") : genre || ""
                        let format = release.formats[0].name

                        // pass in to function
                        buildRelease(artistName, albumName, coverImageUrl, resourceURL, section, format, genreString)

                        // post to database

                        if (section === "wishlist") {
                            postWishlist(resourceURL, albumName, artistName, coverImageUrl, genreString, format)
                        } else if (section === "collection") {
                            postRecord(resourceURL, albumName, artistName, coverImageUrl, genreString, format)
                        }

                        resultsPopup.remove()
                        overlay.style.display = "none"

                        resolve(true)
                    }
                })
            } else {
                collection.innerHTML = "No results found.";
                return false
            }
        })
        .catch(err => {
            collection.innerText = "Error fetching data.";
            console.error(err);
            return false
        });

}

function buildRelease(artist, album, cover_image, url, section, format, genre){
    let collection = document.querySelector("#" + section + "-div")
    let div = document.createElement("div")
    let title = document.createElement("h2")
    let artistP = document.createElement("p")
    let cover = document.createElement("img")

    div.className = "release-div"
    div.id = url.split('/').pop()
    div.dataset.format = format.toLowerCase()
    div.dataset.genre = (genre || "")

    if (section === "wishlist") {
        div.onclick = function () { displayAlbum.call(this, true) }
    } else {
        div.onclick = function () { displayAlbum.call(this, false) }
    }

    title.innerHTML = album || ""
    artistP.innerHTML = artist || ""
    cover.src = cover_image

    div.appendChild(cover)
    div.appendChild(title)
    div.appendChild(artistP)
    collection.appendChild(div)
}

let submitBarcodeBtn = document.querySelector("#submit-barcode-btn")
submitBarcodeBtn.onclick = submitBarcode

let  submitAlbumBtn = document.querySelector("#submit-album-artist-btn")
submitAlbumBtn.onclick = submitAlbumArtist

function deleteVinyl(url, route) {
    console.log("Deleting url:", url)
    fetch(`http://localhost:8080/${encodeURIComponent(route)}?url=${encodeURIComponent(url)}`, {
        method: "DELETE",
        headers: {
            "Authorization": authorizationHeader()
        }
    })
    .then(response => {
        if (response.ok) {
            document.getElementById("overlay").style.display = "none"
            document.getElementById(url.split('/').pop() + "-tracklist").remove()
            document.getElementById(url.split('/').pop()).remove()
        }
    })
    .catch(error => console.error("Error deleting vinyl:", error))
}

function deleteWishlist(url) {
    console.log("Deleting url:", url)
    fetch(`http://localhost:8080/wishlist?url=${encodeURIComponent(url)}`, {
        method: "DELETE",
        headers: {
            "Authorization": authorizationHeader()
        }
    })
    .then(response => {
        if (response.ok) {
            document.getElementById("overlay").style.display = "none"
            document.getElementById(url.split('/').pop() + "-tracklist").remove()
            document.getElementById(url.split('/').pop()).remove()
        }
    })
    .catch(error => console.error("Error deleting vinyl:", error))
}

// album click
// pulls up screen that displays track list and any other important information about the record

function displayAlbum(wishlist = false){
    let url = this.id
    console.log(url)
    resourceURL = 'https://api.discogs.com/releases/' + url
    console.log(resourceURL)

    let existingTracklist = document.getElementById(url + "-tracklist")
    if (existingTracklist != null) {
        existingTracklist.style.display = "flex"
        document.getElementById("overlay").style.display = "block"
    } else {
        // tracklist div
        fetch(`http://localhost:8080/api/discogs/releases?url=${encodeURIComponent(url)}`, {
            headers: {
                "Authorization": authorizationHeader()
            }
        })
            .then(resp => resp.json())
            .then(releaseData => {
                if (releaseData.tracklist && releaseData.tracklist.length > 0) {
                    console.log(releaseData)
                    let tracklistDiv = document.createElement("div");
                    tracklistDiv.className = "tracklist-div"
                    tracklistDiv.id = resourceURL.split("/").pop() + "-tracklist"

                    // album cover
                    let albumCover = document.createElement("img")
                    //albumCover.src = release.images[0].uri
                    albumCover.id = resourceURL.split("/").pop() + "-image"
                    albumCover.className = "focus-image"

                    // arrows
                    let arrowsWrapper = document.createElement("div")
                    arrowsWrapper.className = "arrows-wrapper"

                    let arrowRight = document.createElement("span")
                    arrowRight.className = "material-symbols-outlined"
                    arrowRight.innerHTML = "chevron_right"

                    let arrowLeft = document.createElement("span")
                    arrowLeft.className = "material-symbols-outlined"
                    arrowLeft.innerHTML = "chevron_left"

                    arrowsWrapper.appendChild(arrowLeft)
                    arrowsWrapper.appendChild(arrowRight)

                    // album info
                    let albumTitle = document.createElement("h2")
                    albumTitle.innerHTML = releaseData.title

                    let artistName = document.createElement("p")
                    artistName.innerHTML = releaseData.artists.map(artist => artist.name).join(", ")

                    // format
                    let formatP = document.createElement("p")
                    formatP.innerHTML = "Format: "

                    if (releaseData.formats) {
                        formatP.innerHTML += releaseData.formats[0].name + " - "
                        releaseData.formats[0].descriptions.forEach(description => {
                            formatP.innerHTML += description + " - "
                        })
                        if (releaseData.formats[0].text) {
                            formatP.innerHTML += releaseData.formats[0].text
                        }
                    } else if (release.format) {
                        release.format.forEach(description => {
                            formatP.innerHTML += description + " - "
                        })
                    }

                    formatP.innerHTML = formatP.innerHTML.replace(/ - $/, '')

                    // delete btn
                    let deleteBtn = document.createElement("button")
                    deleteBtn.innerHTML = "DELETE"
                    deleteBtn.className = "delete-button"
                    if (wishlist === false){
                        deleteBtn.onclick = () => deleteVinyl(resourceURL.split('/').pop(), "vinyl")
                    } else {
                        deleteBtn.onclick = () => deleteVinyl(resourceURL.split('/').pop(), "wishlist")
                    }

                    // tracklist
                    let tracklistHeader = document.createElement("h3")
                    tracklistHeader.innerHTML = "Track List"

                    let ul = document.createElement("ul")
                    releaseData.tracklist.forEach(track => {
                        let li = document.createElement("li")
                        let p = document.createElement("p")
                        let time = document.createElement("p")
                        p.innerHTML = track.position + '&emsp;' + track.title
                        time.innerHTML = track.duration
                        li.appendChild(p)
                        li.appendChild(time)
                        ul.appendChild(li)
                    })

                    let tracklistWrapper = document.createElement("div")
                    tracklistWrapper.className = "tracklist-wrapper"
                    tracklistWrapper.appendChild(tracklistHeader)
                    tracklistWrapper.appendChild(ul)

                    let albumInfo = document.createElement("div")
                    albumInfo.className = "album-info"

                    let imageWrapper = document.createElement("div")
                    imageWrapper.className = "image-wrapper"
                    imageWrapper.appendChild(albumCover)
                    imageWrapper.appendChild(arrowsWrapper)

                    albumInfo.appendChild(imageWrapper)
                    albumInfo.appendChild(albumTitle)
                    albumInfo.appendChild(artistName)
                    albumInfo.appendChild(formatP)

                    // close button
                    let closeBtnDiv = document.createElement("div")
                    closeBtnDiv.className = "close-btn-wrapper"
                    let closeBtn = document.createElement("span")
                    closeBtn.className = "material-symbols-outlined"
                    closeBtn.innerHTML = "close"

                    closeBtn.onclick = function () {
                        document.getElementById("overlay").style.display = "none"
                        tracklistDiv.style.display = "none"
                    }

                    closeBtnDiv.appendChild(closeBtn)

                    tracklistDiv.appendChild(albumInfo)
                    tracklistDiv.appendChild(tracklistWrapper)
                    tracklistDiv.appendChild(deleteBtn)
                    tracklistDiv.appendChild(closeBtnDiv)
                    document.querySelector("#overlay").appendChild(tracklistDiv)

                    // image scroll
                    const images = releaseData.images.map(imgObj => imgObj.uri)
                    const imagesAlt = releaseData.images.map(imgObj => imgObj.type)

                    let currentImageIndex = 0

                    albumCover.src = images[currentImageIndex]
                    albumCover.alt = imagesAlt[currentImageIndex]

                    // steppers
                    let stepper = document.createElement("div")
                    stepper.className = "image-stepper"
                    images.forEach((img, idx) => {
                        let dot = document.createElement("span")
                        dot.className = "step-dot" + (idx === currentImageIndex ? " active" : "")
                        dot.onclick = function () {
                            currentImageIndex = idx
                            albumCover.src = images[currentImageIndex]
                            albumCover.alt = imagesAlt[currentImageIndex]
                            updateStepper()
                        }
                        stepper.appendChild(dot)
                    })

                    function updateStepper() {
                        Array.from(stepper.children).forEach((dot, idx) => {
                            dot.className = "step-dot" + (idx === currentImageIndex ? " active" : "")
                        })
                    }

                    imageWrapper.appendChild(stepper)

                    // arrows
                    arrowRight.onclick = function () {
                        currentImageIndex = (currentImageIndex + 1) % images.length
                        albumCover.src = images[currentImageIndex]
                        albumCover.alt = imagesAlt[currentImageIndex]
                        updateStepper()
                    }

                    arrowLeft.onclick = function () {
                        currentImageIndex = (currentImageIndex - 1 + images.length) % images.length
                        albumCover.src = images[currentImageIndex]
                        albumCover.alt = imagesAlt[currentImageIndex]
                        updateStepper()
                    }

                    document.getElementById("overlay").style.display = "block"
                }
            });

    }
}

// nav bar functions

function clearSections(){
    let sections = document.querySelectorAll("section")
    sections.forEach(section => {
        section.style.display = "none"
    })
}

function navCollection(){
    clearSections()
    let collectionSection = document.getElementById("collection-section")
    collectionSection.style.display = "flex"
    document.getElementById("submit-album-artist-btn").onclick = () => submitAlbumArtist("collection")
    document.getElementById("submit-barcode-btn").onclick = () => submitBarcode("collection")
    document.getElementById("submit-search-btn").onclick = () => submitSearch("collection")
}

function displayAddRecordModal(){
    clearSections()
    let section = document.getElementById("add-record-section")
    section.style.display = "flex"
}

function navWishlist(){
    clearSections()
    let wishlistSection = document.getElementById("wishlist-section")
    wishlistSection.style.display = "flex"
    document.getElementById("submit-album-artist-btn").onclick = () => submitAlbumArtist("wishlist")
    document.getElementById("submit-barcode-btn").onclick = () => submitBarcode("wishlist")
    document.getElementById("submit-search-btn").onclick = () => submitSearch("wishlist")
}

function navChat(){
    clearSections()
    let chatSection = document.getElementById("chat-section")
    chatSection.style.display = "flex"
}

clearSections()

// search
function searchCollection(){
    const searchValue = document.getElementById("collection-search-input").value.toLowerCase()
    const releaseDivs = document.querySelectorAll("#collection-div .release-div")

    releaseDivs.forEach(div => {
        const album = div.querySelector("h2")?.textContent.toLowerCase() || ""
        const artist = div.querySelector("p")?.textContent.toLowerCase() || ""
        if (album.includes(searchValue) || artist.includes(searchValue)) {
            div.style.display = ""
        } else {
            div.style.display = "none"
        }
    })
}

// sort
function sortReleaseDivs(by = "album"){
    const collection = document.querySelector("#collection-div")
    const releaseDivs = Array.from(collection.querySelectorAll(".release-div"))

    releaseDivs.sort((a, b) => {
        let aText, bText
        if (by === "artist") {
            aText = a.querySelector("p")?.textContent?.toLowerCase() || ""
            bText = b.querySelector("p")?.textContent?.toLowerCase() || ""
        } else { // default to album
            aText = a.querySelector("h2")?.textContent?.toLowerCase() || ""
            bText = b.querySelector("h2")?.textContent?.toLowerCase() || ""
        }
        return aText.localeCompare(bText)
    })

    releaseDivs.forEach(div => collection.appendChild(div))
    applyCollectionFilters()
}

document.getElementById("sort-dropdown").onchange = function() {
    const value = this.value
    if (value === "album" || value === "artist") {
        sortReleaseDivs(value)
    } 
}

function filterByFormat(format) {
    currentFormatFilter = format || ""
    applyCollectionFilters()
    /*
    const releaseDivs = document.querySelectorAll("#collection-div .release-div")
    releaseDivs.forEach(div => {
        if (!format || div.dataset.format === format.toLowerCase()) {
            div.style.display = ""
        } else {
            div.style.display = "none"
        }
    })
    */
}

document.getElementById("genre-dropdown").onchange = function () {
    const value = this.value
    currentGenreFilter = (value && value !== "Genre:") ? value : ""
    applyCollectionFilters()
    
    /*
    if (value && value !== "Genre:") {
        filterByGenre(value)
    } else {
        filterByGenre("")
    }
    */
}

function filterByGenre(genre) {
    console.log("filtering by genre:", genre)
    const releaseDivs = document.querySelectorAll("#collection-div .release-div")
    releaseDivs.forEach(div => {
        const genres = (div.dataset.genre || "")
            .split(",")
            .map(g => g.trim().toLowerCase())
            .filter(g => g)

        if (!genre || genres.includes(genre.toLowerCase())) {
            div.style.display = ""
        } else {
            div.style.display = "none"
        }
    })
}

function applyCollectionFilters() {
    const releaseDivs = document.querySelectorAll("#collection-div .release-div")
    releaseDivs.forEach(div => {
        const formatMatch = !currentFormatFilter || div.dataset.format === currentFormatFilter.toLowerCase()

        const genres = (div.dataset.genre || "")
            .split(",")
            .map(g => g.trim().toLowerCase())
            .filter(g => g)
        const genreMatch = !currentGenreFilter || genres.includes(currentGenreFilter.toLowerCase())

        div.style.display = (formatMatch && genreMatch) ? "" : "none"
    })
}

// --- Agent Chat ---

// Chat functionality
function appendMessage(content, isUser = false) {
    const chatMessages = document.getElementById("chat-messages");
    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message ${isUser ? "user" : "agent"}`;
    
    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Auto-scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendChatMessage() {
    const chatInput = document.getElementById("chat-input");
    const submitBtn = document.getElementById("chat-submit-btn");
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Display user message
    appendMessage(message, true);
    chatInput.value = "";
    
    // Disable button while loading
    submitBtn.disabled = true;
    submitBtn.textContent = "Loading...";

    // Show loading bubble
    const loadingBubble = document.createElement("div");
    loadingBubble.className = "loading-bubble";
    loadingBubble.innerHTML = `
        <span class="loading-dot"></span>
        <span class="loading-dot"></span>
        <span class="loading-dot"></span>
    `;
    const chatMessages = document.getElementById("chat-messages");
    const loadingMessageDiv = document.createElement("div");
    loadingMessageDiv.className = "chat-message agent";
    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    contentDiv.appendChild(loadingBubble);
    loadingMessageDiv.appendChild(contentDiv);
    chatMessages.appendChild(loadingMessageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        // Send to backend agent
        const response = await fetch("http://localhost:8080/api/assistant/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": authorizationHeader()
            },
            body: JSON.stringify({ query: message })
        });
        
        if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
        }
        
        const data = await response.json();

        // Remove loading bubble
        loadingMessageDiv.remove();

        appendMessage(data.response, false);
        
    } catch (error) {
        console.error("Chat error:", error);
        loadingMessageDiv.remove();
        appendMessage("Sorry, I encountered an error. Please try again.", false);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Send";
        chatInput.focus();
    }
}

// Event listeners for chat
document.getElementById("chat-submit-btn").onclick = sendChatMessage;
document.getElementById("chat-input").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        sendChatMessage();
    }
});

// Check if Spotify connection was successful
function checkSpotifyConnection() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('spotify_connected') === 'true') {
        alert("Spotify connected successfully!");
        // Clear the URL parameter
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

// Call on page load
checkSpotifyConnection();

function openSpotifyLogin() {
    const sessionID = localStorage.getItem('sessionID');
    if (!sessionID) {
        alert('No session ID found. Please reload or log in first.');
        return;
    }
    // navigate to backend login endpoint with our session id so server can persist PKCE verifier
    window.location.href = `http://localhost:8080/spotify/login?session_id=${encodeURIComponent(sessionID)}`;
}