function login_formatting(){
    let psswrd_txt = document.getElementById("psswrd_txt");
    let cont_buttn = document.getElementById("cont_btn");
    let usr_input = document.getElementById("usr_input");
    let psswrd_input = document.getElementById("psswrd_input");

    const usrLen = usr_input.value.trim().length;
    const psswdLen = psswrd_input.value.trim().length;
    if (usrLen > 0 && usrLen <= 20){
        psswrd_txt.innerHTML = "and the password?";
        psswrd_input.style.display="block";
        if (psswdLen >= 8){
            cont_buttn.style.display = "block";
        }
        else{
            cont_buttn.style.display = "none";
        }
        
    }   
    else if (usrLen > 0 && usrLen <= 20){
        psswrd_txt.innerHTML = "and the password?";
        cont_buttn.style.display = "none";
    }
    else{
        psswrd_txt.innerHTML = "";
        cont_buttn.style.display = "none";
        psswrd_input.style.display="none";
    }

}

function submit_login_info(){
    document.getElementById("login_details").submit();
}