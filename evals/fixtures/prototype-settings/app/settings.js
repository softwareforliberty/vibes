import { settings } from "./data.js";

// Renders every section of the settings as one long form.
const root = document.querySelector("#settings");
for (const [section, values] of Object.entries(settings)) {
  const block = document.createElement("fieldset");
  block.innerHTML = `<legend>${section}</legend>`;
  for (const [key, value] of Object.entries(values)) {
    const row = document.createElement("label");
    row.textContent = `${key}: ${value}`;
    block.append(row);
  }
  root.append(block);
}
