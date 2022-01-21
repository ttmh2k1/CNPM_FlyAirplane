function checkBooking(maxE, maxB){
    const economy = document.getElementById('noEconomy')
    const business = document.getElementById('noBusiness')
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
    else {
        business.setCustomValidity("")
        economy.setCustomValidity("")
        valid = true
    }
    economy.reportValidity()
    business.reportValidity()
    return valid
}


function getTotalPrice(Eprice, Bprice){
    try {
        let nE = parseInt(document.getElementById('noEconomy').value) // số lượng vé Economy
        let nB = parseInt(document.getElementById('noBusiness').value) // số lượng vé Business
        if(nE >= 0 && nB >=0) {
            let total = nE * Eprice + nB * Bprice
            document.getElementById('total').value = total.toString() + ' VND'
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