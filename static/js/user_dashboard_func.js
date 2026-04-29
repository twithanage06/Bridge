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

function get_file_details(space_left){
    const fileInput = document.getElementById('file_to_upload');
    const infoBox = document.getElementById('file-info');
    const upload_btn = document.getElementById('upload_btn');
    // Check if a file was actually selected
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0]; // Grab the first file
        
        const fileName = file.name;
        const fileSize = Number((file.size / 1024).toFixed(2)); // Convert bytes to KB
        const number_space_left = Number(space_left);
        const fileType = file.type || "Unknown Type";


        // Display the details
        if (fileSize > number_space_left) {
            upload_btn.style.display = "none";
            infoBox.innerHTML = `
            <strong>The file is too big for the selected drive. Please free up space or choose another file.<br> Space Left: ${number_space_left} KB <br> File Size: ${fileSize} KB</strong> <br>
        `;
        }
        else {
            upload_btn.style.display = "inline-flex";
            const space_left_after = (number_space_left - fileSize)/1000
            infoBox.innerHTML = `
            <strong>Selected:</strong> ${fileName}<br>
            <strong>Size:</strong> ${fileSize} KB<br>
            <strong>Type:</strong> ${fileType} <br>
            <strong>Space Left After This File:</strong> ${space_left_after} MB
        `;
        }
    } else {
        infoBox.innerHTML = "";
    }
}