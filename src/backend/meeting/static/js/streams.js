const APP_ID = '7a9556cdfd984af3805fe3fb809ebf80'
const TOKEN = sessionStorage.getItem('token')
const CHANNEL = sessionStorage.getItem('room')
let UID = sessionStorage.getItem('UID')
let NAME = sessionStorage.getItem('name')
let call_durations = sessionStorage.getItem('duration')
const client = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' })

let localTracks = []
let remoteUsers = {}

let joinAndDisplayLocalStream = async() => {
    document.getElementById('room-name').innerText = CHANNEL

    client.on('user-published', handleUserJoined)
    client.on('user-left', handleUserLeft)

    try {
        UID = await client.join(APP_ID, CHANNEL, TOKEN, UID)
    } catch (error) {
        console.error(error)
        window.open('/', '_self')
    }

    localTracks = await AgoraRTC.createMicrophoneAndCameraTracks()
        //mine code
    const devices = await navigator.mediaDevices.enumerateDevices();

    // Filter the devices to get only video inputs (cameras)
    const cameras = devices.filter(device => device.kind === 'videoinput');
    var cam = cameras['1'].deviceId
        // Log the cameras
        // end mine code
    let member = await createMember()

    let player = `<div  class="video-container" id="user-container-${UID}">
                     <div class="video-player" id="user-${UID}"></div>
                     <div class="username-wrapper"><span class="user-name">${member.name}</span></div>
                  </div>`

    document.getElementById('video-streams').insertAdjacentHTML('beforeend', player)
    localTracks[1].play(`user-${UID}`)
    await client.publish([localTracks[0], localTracks[1]])
    durationTimeout = setTimeout(leaveAndRemoveLocalStream, call_durations * 60 * 1000);
}

let handleUserJoined = async(user, mediaType) => {
    remoteUsers[user.uid] = user
    await client.subscribe(user, mediaType)

    if (mediaType === 'video') {
        let player = document.getElementById(`user-container-${user.uid}`)
        if (player != null) {
            player.remove()
        }

        let member = await getMember(user)

        player = `<div  class="video-container" id="user-container-${user.uid}">
            <div class="video-player" id="user-${user.uid}"></div>
            <div class="username-wrapper"><span class="user-name">${member.name}</span></div>
        </div>`

        document.getElementById('video-streams').insertAdjacentHTML('beforeend', player)
        user.videoTrack.play(`user-${user.uid}`)
    }

    if (mediaType === 'audio') {
        user.audioTrack.play()
    }
}

let handleUserLeft = async(user) => {
    delete remoteUsers[user.uid]
    document.getElementById(`user-container-${user.uid}`).remove()
}

let leaveAndRemoveLocalStream = async() => {
    clearTimeout(durationTimeout);
    for (let i = 0; localTracks.length > i; i++) {
        localTracks[i].stop()
        localTracks[i].close()
    }

    await client.leave()
        //This is somewhat of an issue because if user leaves without actaull pressing leave button, it will not trigger
    deleteMember()
    window.open('/video_call/', '_self')
}

let toggleCamera = async(e) => {
    if (localTracks[1].muted) {
        await localTracks[1].setMuted(false)
        e.target.style.backgroundColor = '#fff'
    } else {
        await localTracks[1].setMuted(true)
        e.target.style.backgroundColor = 'rgb(255, 80, 80, 1)'
    }
}

let switchCamera = async(e) => {
    // Stop the current camera track
    await client.unpublish(localTracks[1])
    localTracks[1].stop()
    localTracks[1].close()
    const devices = await navigator.mediaDevices.enumerateDevices();

    // Filter the devices to get only video inputs (cameras)
    const cameras = devices.filter(device => device.kind === 'videoinput');
    // Create a new camera track with the other camera device
    localTracks[1] = await AgoraRTC.createCameraVideoTrack({ cameraId: cameras['1'].deviceId })

    // Publish the new camera track

    await client.publish(localTracks[1])

    // Play the new camera track
    var newId = "switch-camera-btn-back";

    // Assign the new ID using Django template syntax
    document.getElementById("front_cammer").style.display = "none";
    document.getElementById("back_cammer").style.display = "block";


    localTracks[1].play(`user-${UID}`)
    if (localTracks[1].muted) {
        e.target.style.backgroundColor = 'rgb(255, 80, 80, 1)'
    } else {
        e.target.style.backgroundColor = '#fff'
    }
}

let switchCamerafront = async(e) => {

    // Stop the current camera track
    await client.unpublish(localTracks[1])
    localTracks[1].stop()
    localTracks[1].close()
    const devices = await navigator.mediaDevices.enumerateDevices();

    // Filter the devices to get only video inputs (cameras)
    const cameras = devices.filter(device => device.kind === 'videoinput');
    // Create a new camera track with the other camera device
    localTracks[1] = await AgoraRTC.createCameraVideoTrack({ cameraId: cameras['0'].deviceId })

    // Publish the new camera track

    await client.publish(localTracks[1])

    // Play the new camera track
    localTracks[1].play(`user-${UID}`)

    document.getElementById("front_cammer").style.display = "block";
    document.getElementById("back_cammer").style.display = "none";

    // Toggle the button background color
    if (localTracks[1].muted) {
        e.target.style.backgroundColor = 'rgb(255, 80, 80, 1)'
    } else {
        e.target.style.backgroundColor = '#fff'
    }
}


let toggleMic = async(e) => {
    if (localTracks[0].muted) {
        await localTracks[0].setMuted(false)
        e.target.style.backgroundColor = '#fff'
    } else {
        await localTracks[0].setMuted(true)
        e.target.style.backgroundColor = 'rgb(255, 80, 80, 1)'
    }
}

let createMember = async() => {
    let response = await fetch('/create_member/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'name': NAME, 'room_name': CHANNEL, 'UID': UID })
    })
    let member = await response.json()
    return member
}


let getMember = async(user) => {
    let response = await fetch(`/get_member/?UID=${user.uid}&room_name=${CHANNEL}`)
    let member = await response.json()
    return member
}


let deleteMember = async() => {
    let response = await fetch('/delete_member/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'name': NAME, 'room_name': CHANNEL, 'UID': UID })
    })
    let member = await response.json()
}

window.addEventListener("beforeunload", deleteMember);

joinAndDisplayLocalStream()

document.getElementById('leave-btn').addEventListener('click', leaveAndRemoveLocalStream)
document.getElementById('camera-btn').addEventListener('click', toggleCamera)
document.getElementById('switch-camera-btn').addEventListener('click', switchCamera)

document.getElementById('switch-camera-btn-back').addEventListener('click', switchCamerafront)
document.getElementById('mic-btn').addEventListener('click', toggleMic)