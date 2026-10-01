// Copyright (c) 2026 cpetersen4. See LICENSE for personal-use terms.
// Run in Illustrator: File > Scripts > Other Script.
// Uses the roster CSV only to identify names; no real names are embedded here.
(function () {
    var root = new File($.fileName).parent.parent;
    var target = new File(root.fsName + '/templates/score-sheet-stickers-2026.ai');
    var roster = File.openDialog('Select the original roster CSV or TXT');
    if (!roster) throw new Error('No roster selected. Nothing changed.');
    roster.encoding = 'UTF-8';
    if (!roster.open('r')) throw new Error('Cannot read roster.');
    var raw = roster.read().replace(/^\uFEFF/, '');
    roster.close();

    // CSV parser: quoted commas, escaped quotes, and Windows line endings.
    function parseCSV(text) {
        var rows = [], row = [], field = '', quoted = false;
        for (var i = 0; i < text.length; i++) {
            var c = text.charAt(i);
            if (c === '"') {
                if (quoted && text.charAt(i + 1) === '"') { field += '"'; i++; }
                else quoted = !quoted;
            } else if (c === ',' && !quoted) { row.push(field); field = ''; }
            else if ((c === '\r' || c === '\n') && !quoted) {
                row.push(field); rows.push(row); row = []; field = '';
                if (c === '\r' && text.charAt(i + 1) === '\n') i++;
            } else field += c;
        }
        if (quoted) throw new Error('Unclosed quote in roster CSV.');
        if (field.length || row.length) { row.push(field); rows.push(row); }
        return rows;
    }
    function trim(s) { return s.replace(/^\s+|\s+$/g, ''); }
    function pad(n) { return n < 10 ? '0' + n : '' + n; }
    function escapeRE(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

    var rows = parseCSV(raw), replacements = [], counts = {};
    var nameColumn = -1, roleColumn = -1;
    for (var h = 0; h < rows[0].length; h++) {
        var header = trim(rows[0][h]).toLowerCase();
        if (header === 'name') nameColumn = h;
        if (header === 'role') roleColumn = h;
    }
    if (nameColumn < 0 || roleColumn < 0) throw new Error('CSV needs name and role columns.');
    for (var r = 1; r < rows.length; r++) {
        if (rows[r].length === 1 && !trim(rows[r][0])) continue;
        var name = trim(rows[r][nameColumn] || '');
        var role = trim(rows[r][roleColumn] || '');
        if (!name || !/^(Player|Head Coach|Assistant Coach)$/i.test(role))
            throw new Error('Missing name or unsupported role on CSV row ' + (r + 1));
        var canonical;
        if (role.toLowerCase() === 'player') { canonical = 'Player'; }
        else if (role.toLowerCase() === 'head coach') { canonical = 'Head Coach'; }
        else { canonical = 'Asst Coach'; }
        counts[canonical] = (counts[canonical] || 0) + 1;
        replacements.push({name: name, value: canonical + ' ' + pad(counts[canonical])});
    }
    // Longer names first prevents a first name matching part of a coach's name.
    replacements.sort(function (a, b) { return b.name.length - a.name.length; });
    var doc = null;
    for (var d = 0; d < app.documents.length; d++) {
        if (app.documents[d].fullName.fsName.toLowerCase() === target.fsName.toLowerCase())
            doc = app.documents[d];
    }
    if (!doc) doc = app.open(target);
    var changes = [];
    for (var f = 0; f < doc.textFrames.length; f++) {
        var frame = doc.textFrames[f], content = frame.contents, edits = [];
        for (var n = 0; n < replacements.length; n++) {
            var item = replacements[n];
            var re = new RegExp('(^|[^A-Za-z])(' + escapeRE(item.name) + ')(?=$|[^A-Za-z])', 'g');
            var match;
            while ((match = re.exec(content)) !== null) {
                edits.push({start: match.index + match[1].length, length: item.name.length, value: item.value});
            }
        }
        if (/^PARK\d+[BG]\s+.+$/.test(trim(content)))
            edits.push({start: 0, length: content.length, value: 'Sample Team'});
        if (edits.length) changes.push({frame: frame, edits: edits});
    }
    var dryRun = typeof scoreSheetDryRun !== 'undefined' && scoreSheetDryRun;
    if (!dryRun && changes.length) {
        // Back up both the saved file and any unsaved state before changing text.
        var backup = new File(Folder.temp.fsName + '/score-sheet-before-obfuscation-' + new Date().getTime() + '.ai');
        if (!target.copy(backup.fsName)) throw new Error('Backup failed. Nothing changed.');
        if (!doc.saved) {
            var options = new IllustratorSaveOptions(); options.pdfCompatible = true;
            doc.saveAs(backup, options);
            doc.saveAs(target, options);
        }
        for (var x = 0; x < changes.length; x++) {
            var change = changes[x];
            change.edits.sort(function (a, b) { return b.start - a.start; });
            for (var e = 0; e < change.edits.length; e++) {
                var edit = change.edits[e], range = change.frame.textRange;
                range.start = edit.start; range.end = edit.start + edit.length;
                range.contents = edit.value;
            }
        }
        doc.save();
        app.redraw();
    }
    var report = new File(Folder.temp.fsName + '/score-sheet-obfuscation-result.txt');
    report.open('w');
    report.writeln((dryRun ? 'Dry run' : 'Saved') + ': ' + changes.length + ' text frames');
    for (var k = 0; k < replacements.length; k++) report.writeln(replacements[k].value);
    if (typeof backup !== 'undefined') report.writeln('Backup: ' + backup.fsName);
    report.close();
}());
