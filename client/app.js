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
        await fetchBarcode(entry.barcode, "barcode", "collection", entry.url)
    }
    /*
    .then(response => response.json())
    .then(function (data) {
        console.log(data)
        data.forEach(entry => {
            fetchBarcode(entry.barcode, "barcode", entry.url)
        })
    })
    .catch(error =>{
        console.error("Error fetching collection:", error)
    })
    */
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
        await fetchBarcode(entry.barcode, "barcode", "wishlist", entry.url)
    }
}

// submit
let resourceURL = ""
let token = 'MWfUKFbFxCTMlxIxSXnEUIxGpNrNSJoMlHutkiIv'
let artistName = '' 
let albumName = ''
let releaseBarcode = ''

function submitBarcode(){
    let barcode = document.querySelector("#barcode-input").value.replaceAll(' ', '')
    document.querySelector("#barcode-input").value = ""

    let existingRecord = document.getElementById(barcode.replaceAll(' ', ''))
    if (existingRecord != null){
        if (confirm("You already have this barcode recorded, record again?")) {
            fetchBarcode(barcode, "barcode", "collection").then(success => {
                if (success){
                    postRecord(barcode)
                }
            })
        }
    } else {
        fetchBarcode(barcode, "barcode", "collection").then(success => {
            if (success){
                console.log("Fetch successful")
                postRecord(barcode)
            }
        })
    }
}

function submitAlbumArtist(){
    let artistInput = document.querySelector("#artist-input").value
    document.querySelector("#artist-input").value = ''
    let albumInput = document.querySelector("#album-input").value
    document.querySelector("#album-input").value = ''
    
    let title = albumInput + '&artist=' + artistInput
    // encoding twice screws it up
    console.log(title)

    fetchBarcode({release_title: albumInput, artist: artistInput}, "release_title", "collection").then(success => {
        if (success){
            console.log("Fetch successful")
            console.log(releaseBarcode)
            postRecord(releaseBarcode)
        }
    })
}

function submitBarcodeWishlist(){
    let barcode = document.querySelector("#barcode-input").value.replaceAll(' ', '')
    document.querySelector("#barcode-input").value = ""

    let existingRecord = document.getElementById(barcode.replaceAll(' ', ''))
    if (existingRecord != null){
        if (confirm("You already have this barcode recorded, record again?")) {
            fetchBarcode(barcode, "barcode", "wishlist").then(success => {
                if (success){
                    postWishlist(barcode)
                }
            })
        }
    } else {
        fetchBarcode(barcode, "barcode", "wishlist").then(success => {
            if (success){
                console.log("Fetch successful")
                postWishlist(barcode)
            }
        })
    }
}

function submitAlbumArtistWishlist(){
    let artistInput = document.querySelector("#artist-input").value
    document.querySelector("#artist-input").value = ''
    let albumInput = document.querySelector("#album-input").value
    document.querySelector("#album-input").value = ''
    
    let title = albumInput + '&artist=' + artistInput
    // encoding twice screws it up
    console.log(title)

    fetchBarcode({release_title: albumInput, artist: artistInput}, "release_title", "wishlist").then(success => {
        if (success){
            console.log("Fetch successful")
            console.log(releaseBarcode)
            postWishlist(releaseBarcode)
        }
    })
}

function postRecord(barcode){
    fetch('http://localhost:8080/vinyl', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': authorizationHeader()
        },
        body: `url=${encodeURIComponent(resourceURL)}&barcode=${encodeURIComponent(barcode)}&album=${encodeURIComponent(albumName)}&artist=${encodeURIComponent(artistName)}`
    })
    .then(response => {
        if (response.status === 201){
            clearSections()
            navCollection()
        } else {
            alert("Error: Could not save record. Please try again")
        }
    })
    .catch(() => {
        alert("Network error: Could not connect to server.")
    })
}

function postWishlist(barcode){
    fetch('http://localhost:8080/wishlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': authorizationHeader()
        },
        body: `url=${encodeURIComponent(resourceURL)}&barcode=${encodeURIComponent(barcode)}&album=${encodeURIComponent(albumName)}&artist=${encodeURIComponent(artistName)}`
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


function fetchBarcode(barcode, search_type, section, url = null){
    let collection = document.querySelector("#" + section + "-div")

    if (url) {
        return fetch(`${url}?token=${token}`)
        .then(response => response.json())
        .then(release => {
            console.log("Fetch with url")
            console.log(release)
            let div = document.createElement("div")
            let title = document.createElement("h2")
            let artist = document.createElement("p")
            let cover = document.createElement("img")

            artistName = release.artists[0].name
            albumName = release.title

            let scannedIdentifier = release.identifiers.find(id => id.description && id.description.toLowerCase() === 'scanned')

            if (scannedIdentifier) {
                releaseBarcode = scannedIdentifier.value
            } else if (release.identifiers.length > 0) {
                releaseBarcode = release.identifiers[0].value
            } else {
                releaseBarcode = release.identifiers[1].value
            }

            resourceURL = release.resource_url

            div.className = "release-div"
            //div.id = release.title.replaceAll(' ', '')
            div.id = resourceURL.split("/").pop()
            if (section === "wishlist"){
                div.onclick = function() { displayAlbum.call(this, true)}
            } else {
                div.onclick = displayAlbum
            }
            title.innerHTML = albumName || release.title
            artist.innerHTML = artistName || ""
            cover.src = release.images[0].uri

            div.appendChild(cover)
            div.appendChild(title)
            div.appendChild(artist)
            collection.appendChild(div)

            return true

        })
        .catch(err =>{
            //collection.innerHTML = "Error fetching data."
            console.error(err)
            return false
        })
    } else if (url == null) {
        let query = ""
        if (typeof barcode === "object") {
            query = Object.entries(barcode)
                .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
                .join("&")
        } else {
            query = `${search_type}=${encodeURIComponent(barcode)}`
        }
        return fetch(`https://api.discogs.com/database/search?${query}&type=${encodeURIComponent('release')}&token=${token}`)
        // add type to search 
            .then(response => response.json())
            .then(data => {
                if (data.results && data.results.length > 0) {
                    return new Promise((resolve) => {
                        // confirm correct album
                        let resultsPopup = document.createElement("div")
                        resultsPopup.className = "results-popup"
                        data.results.forEach((result, idx) => {
                            let resultDiv = document.createElement("div")
                            resultDiv.className = "result-div"
                            let leftCol = document.createElement("div")
                            leftCol.className = "left-col"

                            let title = document.createElement("h2")
                            let artist = document.createElement("p")
                            let cover = document.createElement("img")

                            const titleParts = result.title.split(" - ")
                            artistName = titleParts[0]
                            albumName = titleParts[1]

                            title.innerHTML = albumName || result.title
                            artist.innerHTML = artistName || ""
                            cover.src = result.cover_image

                            leftCol.appendChild(cover)
                            leftCol.appendChild(title)
                            leftCol.appendChild(artist)

                            // format
                            let formatP = document.createElement("p")
                            formatP.innerHTML = "Format: "

                            if (result.formats) {
                                formatP.innerHTML += result.formats[0].name + " - "
                                result.formats[0].descriptions.forEach(description => {
                                    formatP.innerHTML += description + " - "
                                })
                                if (result.formats[0].text) {
                                    formatP.innerHTML += result.formats[0].text
                                }
                            } else if (result.format) {
                                result.format.forEach(description => {
                                    formatP.innerHTML += description + " - "
                                })
                            }

                            formatP.innerHTML = formatP.innerHTML.replace(/ - $/, '')

                            leftCol.appendChild(formatP)
                            resultDiv.appendChild(leftCol)

                            // yes button
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

                        function handleResultSelection(selectedIdx) {
                            const release = data.results[selectedIdx]

                            let div = document.createElement("div")
                            let title = document.createElement("h2")
                            let artist = document.createElement("p")
                            let cover = document.createElement("img")

                            console.log(release)

                            const titleParts = release.title.split(" - ")
                            artistName = titleParts[0]
                            albumName = titleParts[1]

                            resourceURL = release.resource_url

                            div.className = "release-div"
                            //div.id = release.title.replaceAll(' ', '')
                            div.id = resourceURL.split('/').pop()
                            if (section === "wishlist"){
                                div.onclick = function() { displayAlbum.call(this, true)}
                            } else {
                                div.onclick = displayAlbum
                            }
                            title.innerHTML = albumName || release.title
                            artist.innerHTML = artistName || ""
                            cover.src = release.cover_image

                            div.appendChild(cover)
                            div.appendChild(title)
                            div.appendChild(artist)
                            collection.appendChild(div)

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
        fetch(`${resourceURL}?token=${token}`)
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
    document.getElementById("submit-album-artist-btn").onclick = submitAlbumArtist
    document.getElementById("submit-barcode-btn").onclick = submitBarcode
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
    document.getElementById("submit-album-artist-btn").onclick = submitAlbumArtistWishlist
    document.getElementById("submit-barcode-btn").onclick = submitBarcodeWishlist
}

clearSections()