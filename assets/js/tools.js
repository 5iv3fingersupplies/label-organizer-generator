(function () {
  function num(form, name) {
    const field = form.querySelector(`[name="${name}"]`);
    return field ? Number(field.value || 0) : 0;
  }
  function val(form, name) {
    const field = form.querySelector(`[name="${name}"]`);
    return field ? String(field.value || "") : "";
  }
  function line(text) {
    return `<li>${text}</li>`;
  }
  function money(value) {
    return `$${Math.max(0, value).toFixed(2)}`;
  }
  function escaped(text) {
    return String(text).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  const handlers = {
    worksheet_math(form) {
      const count = Math.max(4, Math.min(80, num(form, "count") || 20));
      const max = Math.max(5, Math.min(144, num(form, "max") || 20));
      const op = val(form, "operation") || "+";
      const rows = [];
      for (let i = 1; i <= count; i += 1) {
        const a = (i * 7) % max + 1;
        const b = (i * 11) % max + 1;
        const answer = op === "x" ? a * b : op === "-" ? Math.max(a, b) - Math.min(a, b) : a + b;
        rows.push(`<div class="worksheet-row"><span>${op === "-" ? Math.max(a, b) : a} ${op} ${op === "-" ? Math.min(a, b) : b} = ____</span><small>${answer}</small></div>`);
      }
      return `<h3>Printable drill</h3><p>${count} problems. Answers appear in small type for quick checking.</p><div class="worksheet">${rows.join("")}</div>`;
    },
    label_sheet(form) {
      const raw = val(form, "items") || "Sample, Practice, Review, Done";
      const title = val(form, "title") || "Printable sheet";
      const items = raw.split(/[\n,]+/).map((item) => item.trim()).filter(Boolean).slice(0, 48);
      return `<h3>${escaped(title)}</h3><div class="label-grid">${items.map((item) => `<span>${escaped(item)}</span>`).join("")}</div><p>Use print preview to save as PDF.</p>`;
    },
    pricing(form) {
      const materials = num(form, "materials");
      const hours = num(form, "hours");
      const rate = num(form, "rate");
      const overhead = num(form, "overhead");
      const margin = num(form, "margin") / 100;
      const cost = materials + hours * rate + overhead;
      const price = cost / Math.max(0.05, 1 - margin);
      return `<h3>Suggested starting price: ${money(price)}</h3><ul>${line(`Base cost: ${money(cost)}`)}${line(`Target margin: ${(margin * 100).toFixed(0)}%`)}${line("Review market fit before publishing; this is cost math, not a promise of sales.")}</ul>`;
    },
    materials(form) {
      const bulk = num(form, "bulkCost");
      const units = Math.max(1, num(form, "units"));
      const used = Math.max(0.01, num(form, "used"));
      const waste = num(form, "waste") / 100;
      const perUnit = (bulk / units) * used * (1 + waste);
      return `<h3>Material cost per item: ${money(perUnit)}</h3><ul>${line(`Waste buffer included: ${(waste * 100).toFixed(0)}%`)}${line("Add packaging, platform fees, and labor separately.")}</ul>`;
    },
    break_even(form) {
      const fixed = num(form, "fixed");
      const profit = Math.max(0.01, num(form, "profit"));
      const buffer = num(form, "buffer") / 100;
      const units = Math.ceil((fixed * (1 + buffer)) / profit);
      return `<h3>Break-even target: ${units} sales</h3><ul>${line(`Fixed cost with buffer: ${money(fixed * (1 + buffer))}`)}${line("Use this before booking booths or ordering event-specific display materials.")}</ul>`;
    },
    shipping(form) {
      const item = num(form, "itemWeight");
      const packageWeight = num(form, "packageWeight");
      const buffer = num(form, "buffer") / 100;
      const total = (item + packageWeight) * (1 + buffer);
      return `<h3>Estimated packed weight: ${total.toFixed(1)} oz</h3><ul>${line("Verify with a physical scale before buying labels.")}${line("Round up for packaging variation.")}</ul>`;
    },
    comparison(form) {
      const fit = num(form, "fit");
      const ease = num(form, "ease");
      const margin = num(form, "marginScore");
      const repeat = num(form, "repeat");
      const score = Math.round(((fit * 3) + (ease * 2) + (margin * 3) + (repeat * 2)) / 10 * 10);
      return `<h3>Decision score: ${score}/10</h3><ul>${line(score >= 7 ? "Promising enough to test." : "Needs a tighter job before buying supplies.")}${line("Use the score to narrow choices, not to replace judgment.")}</ul>`;
    },
    inventory(form) {
      const bins = Math.max(1, num(form, "bins"));
      const categories = (val(form, "categories") || "Tools, Seasonal, Paper, Cables").split(/[\n,]+/).map((item) => item.trim()).filter(Boolean);
      const labels = [];
      for (let i = 1; i <= bins; i += 1) labels.push(`BIN-${String(i).padStart(2, "0")} ${categories[(i - 1) % categories.length] || "General"}`);
      return `<h3>Inventory labels</h3><div class="label-grid">${labels.map((item) => `<span>${escaped(item)}</span>`).join("")}</div>`;
    },
    paint(form) {
      const length = num(form, "length"), width = num(form, "width"), height = num(form, "height");
      const doors = num(form, "doors"), windows = num(form, "windows"), coats = Math.max(1, num(form, "coats"));
      const coverage = Math.max(50, num(form, "coverage"));
      const area = Math.max(0, 2 * (length + width) * height - doors * 20 - windows * 15);
      const gallons = Math.ceil((area * coats) / coverage);
      return `<h3>Estimated paint: ${gallons} gallon(s)</h3><ul>${line(`Paintable area: ${area.toFixed(0)} sq ft`)}${line("Buy samples and verify wall texture before committing.")}</ul>`;
    },
    curtains(form) {
      const width = num(form, "windowWidth"), height = num(form, "windowHeight"), fullness = num(form, "fullness") || 2;
      return `<h3>Panel coverage target: ${(width * fullness).toFixed(0)} inches</h3><ul>${line(`Rod starting length: ${(width + 8).toFixed(0)} to ${(width + 16).toFixed(0)} inches`)}${line(`Panel length starting point: ${(height + 6).toFixed(0)} inches`)}</ul>`;
    },
    rug(form) {
      const room = num(form, "roomWidth") * num(form, "roomLength");
      const furniture = num(form, "furnitureWidth") * num(form, "furnitureLength");
      const ratio = furniture / Math.max(1, room);
      return `<h3>Starting rug approach</h3><ul>${line(ratio > 0.45 ? "Use a large-area rug path." : "Use a smaller zone rug path.")}${line(`Furniture footprint: ${furniture.toFixed(0)} sq ft`)}</ul>`;
    },
    shelf(form) {
      const height = num(form, "wallHeight"), item = Math.max(1, num(form, "itemHeight")), clearance = num(form, "clearance");
      const shelves = Math.max(1, Math.floor(height / (item + clearance)));
      return `<h3>Estimated shelf openings: ${shelves}</h3><ul>${line(`Opening target: ${(item + clearance).toFixed(1)} inches`)}</ul>`;
    },
    bin_fit(form) {
      const shelfW = num(form, "shelfWidth"), binW = Math.max(1, num(form, "binWidth")), clearance = num(form, "clearance");
      const count = Math.floor((shelfW + clearance) / (binW + clearance));
      return `<h3>${count} bin(s) per shelf row</h3><ul>${line("Confirm exterior dimensions; handles and lids often add width.")}</ul>`;
    },
    budget(form) {
      const total = num(form, "budget");
      const guests = Math.max(1, num(form, "guests"));
      return `<h3>Budget per guest: ${money(total / guests)}</h3><ul>${line(`Food starting bucket: ${money(total * 0.4)}`)}${line(`Decor and supplies bucket: ${money(total * 0.2)}`)}${line(`Buffer: ${money(total * 0.1)}`)}</ul>`;
    },
    servings(form) {
      const guests = num(form, "guests"), hours = num(form, "hours"), buffer = 1 + num(form, "buffer") / 100;
      return `<h3>Supply starting point</h3><ul>${line(`${Math.ceil(guests * 1.2 * buffer)} plates`)}${line(`${Math.ceil(guests * 2.5 * buffer)} napkins`)}${line(`${Math.ceil(guests * hours * 1.25 * buffer)} cups`)}</ul>`;
    },
    beverages(form) {
      const guests = num(form, "guests"), hours = num(form, "hours"), hot = val(form, "hot") === "yes";
      const ounces = guests * hours * (hot ? 16 : 12);
      return `<h3>Drink starting point: ${(ounces / 128).toFixed(1)} gallons</h3><ul>${line("Add water separately for outdoor or hot-weather events.")}</ul>`;
    },
    timeline(form) {
      const setup = num(form, "setup"), eventHours = num(form, "eventHours"), cleanup = num(form, "cleanup");
      return `<h3>Total venue time: ${(setup + eventHours + cleanup).toFixed(1)} hours</h3><ul>${line("Build backwards from guest arrival.")}${line("Keep a 15-minute buffer before food service.")}</ul>`;
    },
    soil(form) {
      const feet = num(form, "length") * num(form, "width") * (num(form, "depth") / 12) * (num(form, "fill") / 100);
      return `<h3>Soil volume: ${feet.toFixed(1)} cubic feet</h3><ul>${line(`Bag estimate at 1.5 cu ft each: ${Math.ceil(feet / 1.5)} bags`)}</ul>`;
    },
    seed_calendar(form) {
      const lead = num(form, "weeks"), crops = val(form, "crops") || "tomatoes, peppers, herbs";
      return `<h3>Seed-starting plan</h3><p>Start ${escaped(crops)} about ${lead} weeks before your target transplant date.</p><ul>${line("Check local frost guidance before planting outside.")}${line("Label trays before watering.")}</ul>`;
    },
    spacing(form) {
      const area = num(form, "length") * num(form, "width") * 144;
      const spacing = Math.max(1, num(form, "spacing"));
      const plants = Math.floor(area / (spacing * spacing));
      return `<h3>Estimated plant count: ${plants}</h3><ul>${line("Leave paths and harvest space if plants spread.")}</ul>`;
    },
    container(form) {
      const plants = Math.max(1, num(form, "plants")), gallons = Math.max(1, num(form, "gallons"));
      return `<h3>Container capacity signal</h3><ul>${line(`${(gallons / plants).toFixed(1)} gallons per plant`)}${line(gallons / plants >= 3 ? "Good starting room for many compact plants." : "Consider larger containers or fewer plants.")}</ul>`;
    },
    watering(form) {
      const containers = num(form, "containers"), beds = num(form, "beds"), heat = val(form, "heat") === "hot" ? 1.35 : 1;
      const gallons = (containers * 0.4 + beds * 6) * heat;
      return `<h3>Weekly watering starting point: ${gallons.toFixed(1)} gallons</h3><ul>${line("Adjust for rain, soil, mulch, and plant stress.")}</ul>`;
    },
    reading_schedule(form) {
      const pages = num(form, "pages"), days = Math.max(1, num(form, "days"));
      return `<h3>Daily target: ${Math.ceil(pages / days)} pages</h3><ul>${line("Add catch-up days for longer chapters.")}${line("Public-domain source text should be checked before creating products.")}</ul>`;
    }
  };
  document.addEventListener("submit", function (event) {
    const form = event.target.closest("form[data-calculator]");
    if (!form) return;
    event.preventDefault();
    const result = form.closest(".tool-shell").querySelector(".result-box");
    const kind = form.dataset.calculator;
    result.innerHTML = handlers[kind] ? handlers[kind](form) : "<p>Tool configuration missing.</p>";
  });
})();
