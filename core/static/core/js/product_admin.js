document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.querySelector('#id_category');
    const subcategorySelect = document.querySelector('#id_subcategory');

    if (!categorySelect || !subcategorySelect) return;

    categorySelect.addEventListener('change', function() {
        const categoryId = this.value;
        fetch(`/core/subcategories-json/?category=${categoryId}`)
            .then(res => res.json())
            .then(data => {
                subcategorySelect.innerHTML = '';
                data.forEach(sub => {
                    const option = document.createElement('option');
                    option.value = sub.id;
                    option.textContent = sub.name;
                    subcategorySelect.appendChild(option);
                });
            });
    });
});
