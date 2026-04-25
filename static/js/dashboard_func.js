function chosen_drive(drive){
    document.getElementById("selected_drive").value = drive;
    document.getElementById("details_form").submit();
}

function chosen_user(username){
    document.getElementById("selected_user").value = username;
    document.getElementById("details_form").submit();
}

function chosen_file(drive){
    document.getElementById("selected_file").value = drive;
    document.getElementById("details_form").submit();
}

function search_term() {
    const searchString = document.getElementById('searchBar').value.toLowerCase();
    const fileRows = document.querySelectorAll('.file-row');
    sessionStorage.setItem('savedSearch', searchString);
    fileRows.forEach((row) => {
        const fileNameCell = row.querySelector('.file-name');
        
        if (fileNameCell) {
            const fileNameText = fileNameCell.textContent.toLowerCase();
            if (fileNameText.includes(searchString)) {
                row.style.display = ''; 
            } else {
                row.style.display = 'none'; 
            }
        }
    });
    
}

window.addEventListener('DOMContentLoaded', () => {
    const rememberedSearch = sessionStorage.getItem('savedSearch');
    
    if (rememberedSearch) {
        const searchBar = document.getElementById('searchBar');
        searchBar.value = rememberedSearch;
        search_term(); 
    }
});


function init_folder(){
    const folder_name = document.getElementById("folder_name").value;
    document.getElementById("details_form").submit();
}