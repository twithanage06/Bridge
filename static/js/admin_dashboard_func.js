function chosen_drive(drive, element){
    document.getElementById("selected_drive").value = drive;
    document.getElementById("selected_user").value = ""; 
    document.getElementById("details_form").submit();
}

function chosen_user(username, element){
    document.getElementById("selected_user").value = username;
    document.getElementById("selected_drive").value = ""; 
    document.getElementById("details_form").submit();
}



