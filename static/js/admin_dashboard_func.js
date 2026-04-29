function chosen_drive(drive, element){
    document.getElementById("selected_drive").value = drive;
    document.getElementById("selected_user").value = ""; // Clear user selection
    document.getElementById("details_form").submit();
}

function chosen_user(username, element){
    document.getElementById("selected_user").value = username;
    document.getElementById("selected_drive").value = ""; // Clear drive selection
    document.getElementById("details_form").submit();
}



