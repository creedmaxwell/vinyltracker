// display all user's saved records
function displayUserCollection(){
    console.log("displaying user collection")
    fetch("http://localhost:8080/vinyl", {
        headers:{
            "Authorization": authorizationHeader()
        }
    })
    .then(response => response.json())
    .then(function (data) {
        console.log(data)
        data.forEach(entry => {
            fetchBarcode(entry.barcode)
        })
    })
    .catch(error =>{
        console.error("Error fetching collection:", error)
    })
}

// submit
let resourceURL = ""
let token = 'MWfUKFbFxCTMlxIxSXnEUIxGpNrNSJoMlHutkiIv'

function submitBarcode(){
    let barcode = document.querySelector("#barcode-input").value
    document.querySelector("#barcode-input").value = ""

    let existingRecord = document.getElementById(barcode.replaceAll(' ', ''))
    if (existingRecord != null){
        if (confirm("You already have this barcode recorded, record again?")) {
            fetchBarcode(barcode)
        }
    } else {
        const success = fetchBarcode(barcode)
        if (success){
            fetch('http://localhost:8080/vinyl', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Authorization': authorizationHeader()
                        },
                        body: `barcode=${encodeURIComponent(barcode)}`
                    })
        }
    }
}

function fetchBarcode(barcode){
    let collection = document.querySelector("#collection-div")

    fetch(`https://api.discogs.com/database/search?barcode=${encodeURIComponent(barcode)}&token=${token}`)
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                const release = data.results[0];
                let div = document.createElement("div")
                let title = document.createElement("h2")
                let cover = document.createElement("img")

                console.log(release)

                div.className = "release-div"
                //div.id = release.title.replaceAll(' ', '')
                div.id = barcode.replaceAll(' ', '')
                div.onclick = displayAlbum
                title.innerHTML = release.title
                cover.src = release.cover_image

                div.appendChild(cover)
                div.appendChild(title)
                collection.appendChild(div)

                return true

            } else {
                collection.innerHTML = "No results found.";
            }
        })
        .catch(err => {
            collection.innerText = "Error fetching data.";
            console.error(err);
        });
}

let submitBtn = document.querySelector("#submit-btn")
submitBtn.onclick = submitBarcode

// album click
// pulls up screen that displays track list and any other important information about the record

function displayAlbum(){
    let barcode = this.id

    let existingTracklist = document.getElementById(barcode + "-tracklist")
    if (existingTracklist != null) {
        console.log("exists")
        existingTracklist.style.display = "flex"
        document.getElementById("overlay").style.display = "block"
    } else {
        console.log("doesnt exist")
        fetch(`https://api.discogs.com/database/search?barcode=${encodeURIComponent(barcode)}&token=${token}`)
            .then(response => response.json())
            .then(data => {
                if (data.results && data.results.length > 0) {
                    const release = data.results[0];
                    resourceURL = release.resource_url

                    // tracklist div
                    fetch(`${resourceURL}?token=${token}`)
                        .then(resp => resp.json())
                        .then(releaseData => {
                            if (releaseData.tracklist && releaseData.tracklist.length > 0) {
                                console.log(releaseData)
                                let tracklistDiv = document.createElement("div");
                                tracklistDiv.className = "tracklist-div"
                                tracklistDiv.id = barcode + "-tracklist"

                                // album cover
                                let albumCover = document.createElement("img")
                                albumCover.src = release.cover_image
                                albumCover.id = barcode + "-image"
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

                                let artistName = document.createElement("h3")
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

                                let ul = document.createElement("ul");
                                releaseData.tracklist.forEach(track => {
                                    let li = document.createElement("li");
                                    li.textContent = `${track.position} - ${track.title}`;
                                    ul.appendChild(li);
                                });

                                let leftCol = document.createElement("div")
                                leftCol.className = "left-column"

                                let imageWrapper = document.createElement("div")
                                imageWrapper.className = "image-wrapper"
                                imageWrapper.appendChild(albumCover)
                                imageWrapper.appendChild(arrowsWrapper)

                                leftCol.appendChild(imageWrapper)
                                leftCol.appendChild(albumTitle)
                                leftCol.appendChild(artistName)
                                leftCol.appendChild(formatP)

                                let rightCol = document.createElement("div")
                                rightCol.className = "right-column"

                                rightCol.appendChild(ul)

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

                                tracklistDiv.appendChild(leftCol)
                                tracklistDiv.appendChild(rightCol)
                                tracklistDiv.appendChild(closeBtnDiv)
                                document.querySelector("#overlay").appendChild(tracklistDiv)

                                // image scroll
                                const images = releaseData.images.map(imgObj => imgObj.uri)
                                const imagesAlt = releaseData.images.map(imgObj => imgObj.type)

                                let currentImageIndex = 0

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

                } else {
                    collection.innerHTML = "No results found."
                }
            })
            .catch(err => {
                collection.innerText = "Error fetching data."
                console.error(err)
            });
    }
}
