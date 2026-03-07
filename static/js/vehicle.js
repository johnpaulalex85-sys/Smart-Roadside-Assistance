/* vehicle.js — Dynamic vehicle company dropdown */

const VEHICLE_COMPANIES = {
    'Car': ['Suzuki', 'Toyota', 'Mahindra', 'Hyundai', 'Honda', 'Tata', 'Ford', 'Kia', 'Volkswagen', 'Skoda', 'Renault', 'Nissan', 'MG'],
    'Bike': ['Honda', 'Yamaha', 'KTM', 'Royal Enfield', 'Bajaj', 'TVS', 'Hero', 'Suzuki', 'Kawasaki', 'Ducati'],
    'Truck': ['Tata', 'Ashok Leyland', 'Mahindra', 'Eicher', 'BharathBenz', 'Volvo', 'MAN', 'Force'],
    'Tipper': ['Tata', 'Ashok Leyland', 'Eicher', 'Mahindra', 'BEML'],
    'Van': ['Maruti', 'Tata', 'Force', 'Mahindra', 'Toyota', 'Hyundai', 'Kia'],
};

function updateCompanies() {
    const type = document.getElementById('vehicleType').value;
    const companySel = document.getElementById('vehicleCompany');
    companySel.innerHTML = '<option value="">-- Select Company --</option>';

    const companies = VEHICLE_COMPANIES[type] || [];
    companies.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.textContent = c;
        companySel.appendChild(opt);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const typeEl = document.getElementById('vehicleType');
    if (typeEl) {
        typeEl.addEventListener('change', updateCompanies);
    }
});
