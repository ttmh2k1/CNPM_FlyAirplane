
function checkBooking(maxE, maxB){
    const economy = document.getElementById('noEconomy')
    const business = document.getElementById('noBusiness')
    const customer = document.getElementById("sl1")
    var valid = false
    if (isNaN(economy.value) || parseInt(economy.value) < 0){
        economy.setCustomValidity("not valid")
    }
    else if(isNaN(business.value)|| parseInt(business.value) < 0){
        business.setCustomValidity("not valid")
    }
    else if(parseInt(business.value) + parseInt(economy.value) == 0){
        economy.setCustomValidity("pick number of ticket")
    }
    else if(parseInt(business.value) > maxB){
        business.setCustomValidity("not enough tickets")
    }
    else if(parseInt(economy.value) > maxE){
        economy.setCustomValidity("not enough tickets")
    }
    else if(customer.value == "0"){
        customer.setCustomValidity("Please choose a customer!")
    }
    else {
        valid = true
    }
    economy.reportValidity()
    business.reportValidity()
    customer.reportValidity()
    return valid
}


function getTotalPrice(Eprice, Bprice){
    try {
        let nE = document.getElementById('noEconomy').value
        let nB = document.getElementById('noBusiness').value
        if (nE == "")
            nE = "0"
        if (nB == "")
            nB = "0"
        nE = parseInt(nE) // số lượng vé Economy
        nB = parseInt(nB) // số lượng vé Business
        if(nE >= 0 && nB >=0) {
            let total = nE * Eprice + nB * Bprice
            document.getElementById('total').value = total.toString()
        }
    }catch (err){
    }
}

function prebook(takeOffTime, dateRule, id, nextUrl) {
    var now = new Date()
    var difference = Math.abs(takeOffTime - now)
    days = difference/(1000 * 3600 * 24)
    if (days < parseInt(dateRule)) {
        alert('You must book before ' + dateRule.toString() + ' days')
    }
    else{
        location.replace(nextUrl);
    }
}


function addDays(date, number) {
    const newDate = new Date(date);
    return new Date(newDate.setDate(date.getDate() + number));
}

function showImage(event){
    let imgCon = document.getElementById('avt')
    let files = event.target.files[0]
    if(files){
        imgCon.src = URL.createObjectURL(files)
    }
}

function nextPage(page_cur){
    var nextTag = document.getElementById("page"+(page_cur+1).toString())
    window.location.href = nextTag.href;
}
function previousPage(page_cur){
    var nextTag = document.getElementById("page"+(page_cur-1).toString())
    window.location.href = nextTag.href;
}

function loadCustomer(customers){
    var cid = document.getElementById("sl1").value
    for (let i =0; i< customers.length; i++){
        if (customers[i]['id'].toString() == cid){
            document.getElementById("phone").value = customers[i]["phone"]
            document.getElementById("idNo").value = customers[i]["idNo"]
            break;
        }
    }
    if(cid == "0"){
        document.getElementById("phone").value = ""
        document.getElementById("idNo").value = ""
    }
}

function to_signin(){
    let url = window.location.href
    if (url.includes("signup")){
        location.replace("/login");
    }
}
