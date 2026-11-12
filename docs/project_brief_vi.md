# Dự án Fintech: Ngân hàng có tính lãi công bằng không? (Bản chi tiết)

Nov 5, 2026 · @DanDan

**Chủ đề:** Fintech, mảng tín dụng và lãi suất. Bạn dùng dữ liệu hơn 2 triệu khoản vay có thật của LendingClub (Mỹ, 2007–2018) để kiểm tra xem người vay có đang bị tính lãi đúng với mức rủi ro của họ không.

**Bạn sẽ làm gì:** Khám phá dữ liệu bằng biểu đồ, tự xây một "máy chấm điểm" người vay bằng Python, so sánh nó với cách LendingClub xếp hạng khách hàng từ A đến G, tính mức lãi "công bằng" và thử làm nhà đầu tư trên dữ liệu thật. Cuối cùng, bạn biến toàn bộ kết quả thành một trang web tương tác.

**Bạn sẽ học được gì:**

- **Kiến thức tài chính:** rủi ro vỡ nợ, lãi suất, phần bù rủi ro, tổn thất kỳ vọng, thị trường hiệu quả.
- **Kỹ năng dữ liệu:** Python, xử lý bảng dữ liệu hàng triệu dòng, vẽ biểu đồ, học máy cơ bản, làm app web, dùng Git và GitHub.
- **Tư duy nghiên cứu:** đặt câu hỏi, kiểm chứng bằng dữ liệu, tự phát hiện và sửa sai.

**Đầu ra:** một app web chạy thật có link chia sẻ, một báo cáo nghiên cứu, một kho code trên GitHub và một video demo 2 phút, sẵn sàng đưa vào hồ sơ du học.

**Thời lượng:** 14 tuần, khoảng 2–4 giờ mỗi tuần, có mentor kèm từ đầu đến cuối.

## Dự án này là gì?

Trong 14 tuần, bạn sẽ dùng hơn 2 triệu khoản vay có thật để kiểm tra một câu hỏi mà các nhà đầu tư và ngân hàng luôn đau đầu: **người vay có đang bị tính lãi đúng với mức rủi ro của họ không?**

Khi bạn đi vay, bên cho vay phải đoán xem bạn có trả được nợ hay không. Ai càng có vẻ rủi ro thì càng bị tính lãi cao. Nhưng cách đoán đó có chuẩn không? Có người bị tính lãi quá cao so với mức rủi ro thật, và có người lại được ưu đãi quá mức? Đó là điều bạn sẽ tự tìm ra.

**Điều đặc biệt của dự án:** bạn không chỉ học lý thuyết. Bạn sẽ tự xây một "máy chấm điểm" người vay, đặt nó cạnh cách chấm điểm của một công ty tài chính thật, rồi xem bên nào đúng hơn. Kết quả cuối cùng là một trang web mà bất kỳ ai, kể cả hội đồng tuyển sinh, cũng có thể mở ra và tự tay dùng thử.

## Câu hỏi bạn sẽ trả lời

**Câu hỏi lớn:** LendingClub có tính lãi công bằng với mức rủi ro của từng người vay không?

Để trả lời, bạn sẽ đi qua 4 câu hỏi nhỏ, mỗi câu là một chặng của dự án:

1. **Ai hay không trả được nợ?** Thu nhập, số tiền vay, mục đích vay, lịch sử nợ… yếu tố nào báo hiệu rủi ro rõ nhất?
2. **Máy của bạn có chấm điểm giỏi hơn chuyên gia không?** So "máy chấm điểm" của bạn với hạng A đến G mà LendingClub tự xếp cho khách hàng.
3. **Lãi suất có bù đủ rủi ro không?** Với mỗi hạng, tiền lãi thu được có đủ bù cho tiền mất do người vay không trả nợ không? Hạng nào "đáng đầu tư" nhất?
4. **Ai bị bỏ lại phía sau?** So sánh những người được duyệt vay và những người bị từ chối: họ khác nhau ở điểm nào, và điều đó có công bằng không?

Bạn không cần biết trước câu trả lời. Có thể bạn sẽ thấy LendingClub làm rất tốt, cũng có thể bạn sẽ tìm ra một nhóm khách hàng bị tính lãi sai. Cả hai đều là phát hiện đáng giá, miễn là bạn chứng minh được bằng dữ liệu.

## Dữ liệu bạn sẽ dùng

**LendingClub là ai?** LendingClub là công ty Mỹ từng là [nền tảng cho vay ngang hàng lớn nhất thế giới](https://www.doc.surf/wiki/lendingclub). "Cho vay ngang hàng" nghĩa là người bình thường có thể cho người khác vay tiền qua một trang web, không cần qua ngân hàng. LendingClub chấm điểm người vay, xếp họ vào các hạng từ A (an toàn nhất) đến G (rủi ro nhất), rồi đặt lãi suất theo hạng. Đến cuối năm 2020, công ty [đóng mô hình cho vay ngang hàng](https://www.bankingdive.com/news/lendingclub-peer-to-peer-loans/586841/) và chuyển thành ngân hàng số, nên dữ liệu của bạn ghi lại trọn vẹn một thời kỳ của ngành fintech.

**Dữ liệu gồm gì?** Bộ [LendingClub trên Kaggle](https://www.kaggle.com/wordsforthewise/lending-club) có hai phần, miễn phí và công khai ([quy mô](https://gegznav.github.io/ds-projects/lending-club)):

- **Khoản vay được duyệt:** khoảng 2,26 triệu khoản vay từ 2007 đến 2018, mỗi khoản có 151 thông tin.
- **Đơn bị từ chối:** khoảng 27,6 triệu đơn xin vay bị từ chối, mỗi đơn có 9 thông tin.

Bạn sẽ không dùng hết 151 cột. Đây là những thông tin quan trọng nhất:

| Thông tin | Ý nghĩa đơn giản |
| --- | --- |
| Số tiền vay | Người đó vay bao nhiêu đô la |
| Kỳ hạn | Trả trong 3 năm hay 5 năm |
| Lãi suất | Mức lãi LendingClub tính cho khoản vay |
| Hạng (A–G) | Đánh giá rủi ro của LendingClub: A an toàn nhất, G rủi ro nhất |
| Thu nhập hằng năm | Người vay kiếm được bao nhiêu mỗi năm |
| Tỷ lệ nợ trên thu nhập | Bao nhiêu phần thu nhập đang dùng để trả các khoản nợ khác |
| Điểm tín dụng | Điểm đánh giá lịch sử vay trả của người đó |
| Mục đích vay | Trả nợ thẻ, sửa nhà, mua xe, kinh doanh… |
| Thâm niên làm việc | Đã đi làm bao lâu |
| Kết quả | Đã trả hết nợ, hay không trả được (vỡ nợ) |

**Một điều cần cẩn thận:** nhiều khoản vay trong dữ liệu vẫn đang được trả dở. Nếu tính cả chúng, bạn sẽ tưởng tỷ lệ vỡ nợ thấp hơn thực tế, vì những khoản rủi ro chưa kịp vỡ. Phát hiện và xử lý những "cái bẫy" kiểu này chính là kỹ năng của một nhà phân tích thật, và là chất liệu rất tốt cho bài luận.

## Kiến thức tài chính bạn sẽ học

Đây là những khái niệm mà sinh viên năm nhất ngành Tài chính, Kinh tế sẽ học. Bạn sẽ hiểu chúng qua dữ liệu thật thay vì chỉ đọc định nghĩa.

| Khái niệm | Hiểu đơn giản | Ví dụ trong dự án |
| --- | --- | --- |
| Rủi ro vỡ nợ | Khả năng người vay không trả được tiền | Người vay hạng G có khả năng vỡ nợ cao hơn nhiều so với hạng A |
| Lãi suất | Cái giá của việc mượn tiền | Hạng A trả lãi thấp, hạng G trả lãi cao |
| Phần bù rủi ro | Phần lãi thêm để bù cho việc chấp nhận rủi ro | Vì sao người rủi ro hơn phải trả lãi cao hơn |
| Tổn thất kỳ vọng | Số tiền trung bình dự kiến mất do vỡ nợ | Cho vay 10.000 đô, khả năng vỡ nợ 10%, mất 60% nếu vỡ nợ → kỳ vọng mất 600 đô |
| Lợi nhuận đầu tư | Tiền lời thực tế sau khi trừ tiền mất | So sánh lời lỗ khi chỉ cho hạng A vay với khi cho tất cả các hạng vay |
| Lựa chọn bất lợi | Khi người rủi ro nhất lại là người muốn vay nhất | Vì sao bên cho vay phải cẩn thận với người chấp nhận lãi rất cao |
| Thị trường hiệu quả | Giá cả đã phản ánh hết thông tin có sẵn | Nếu bạn chọn được khoản vay tốt hơn LendingClub, thị trường chưa hiệu quả |

Công thức quan trọng nhất của dự án chỉ cần toán cấp 2:

```latex
\text{Tổn thất kỳ vọng} = \text{Khả năng vỡ nợ} \times \text{Tỷ lệ mất khi vỡ nợ} \times \text{Số tiền cho vay}
```

Nếu tiền lãi thu được lớn hơn tổn thất kỳ vọng, khoản vay có lời. Toàn bộ dự án xoay quanh việc đo chính xác hai con số này.

## App của bạn trông như thế nào

Sản phẩm chính của dự án là một trang web tương tác làm bằng Streamlit, có link để ai cũng mở được. App gồm 4 trang:

| Trang | Người xem làm gì | Người xem thấy gì |
| --- | --- | --- |
| Định giá khoản vay | Nhập thông tin một người vay: thu nhập, số tiền vay, mục đích, điểm tín dụng | Khả năng trả nợ, hạng mà máy của bạn chấm, hạng LendingClub có thể cho, và mức lãi "công bằng" |
| Thử làm nhà đầu tư | Chọn một cách đầu tư, ví dụ "chỉ cho hạng A và B vay" hoặc "chọn theo máy chấm điểm của tôi" | Tiền lời, tiền lỗ thực tế nếu đã đầu tư như vậy trong quá khứ |
| Máy của tôi vs. LendingClub | Xem kết quả so sánh | Bên nào đoán đúng người vỡ nợ hơn, và đúng hơn ở nhóm khách hàng nào |
| Ai bị từ chối? | Lọc theo bang, thu nhập, mục đích vay | Người được duyệt và người bị từ chối khác nhau thế nào |

Bạn có thể tham khảo [một dự án mẫu có cùng cách trình bày](https://github.com/nhamhung/soccer-xg) (chủ đề bóng đá) để hình dung một app hoàn chỉnh trông ra sao.

## Cách làm chi tiết

Phần này mô tả từng bước kỹ thuật. Bạn chưa cần hiểu hết ngay, mentor sẽ giải thích từng bước khi đến chặng đó.

### Bước 1: Làm sạch dữ liệu

- **Chỉ giữ khoản vay đã kết thúc:** trạng thái "Fully Paid" (trả hết) hoặc "Charged Off" (vỡ nợ). Bỏ các khoản "Current", "Late", "In Grace Period".
- **Chỉ giữ khoản vay đã đủ thời gian đáo hạn:** ví dụ khoản vay 3 năm phát hành đến hết 2015. Nếu không, các khoản rủi ro chưa kịp vỡ nợ sẽ làm kết quả đẹp giả tạo.
- **Bỏ các cột "nhìn trước tương lai":** những cột chỉ có sau khi khoản vay đã chạy, như tổng tiền đã trả, tiền thu hồi sau vỡ nợ, ngày trả cuối cùng, điểm tín dụng lần cuối. Dùng chúng để dự đoán là gian lận vô tình.
- **Không dùng hạng và lãi suất làm đầu vào:** đây là "đáp án" của LendingClub, bạn chỉ dùng chúng để so sánh.
- **Lưu dữ liệu gọn:** chỉ giữ khoảng 20–30 cột cần thiết, lưu sang định dạng Parquet để máy chạy nhanh.

### Bước 2: Chọn thông tin đầu vào

Nhóm thông tin bạn sẽ dùng để dự đoán: số tiền và kỳ hạn vay, thu nhập, tỷ lệ nợ trên thu nhập, điểm tín dụng, thâm niên làm việc, tình trạng nhà ở, mục đích vay, mức sử dụng hạn mức thẻ, số lần trễ hạn 2 năm gần nhất, số lần hỏi vay 6 tháng gần nhất, độ dài lịch sử tín dụng. Bạn cũng sẽ tự tạo thông tin mới, ví dụ "khoản trả hằng tháng chiếm bao nhiêu phần trăm thu nhập".

### Bước 3: Xây máy chấm điểm

- **Mô hình 1, hồi quy logistic:** đơn giản, dễ giải thích từng yếu tố tăng hay giảm rủi ro bao nhiêu.
- **Mô hình 2, LightGBM:** mạnh hơn, bắt được những mối quan hệ phức tạp.
- **Chia dữ liệu theo thời gian:** dạy máy bằng khoản vay 2007–2013, kiểm tra bằng khoản vay 2014–2015. Đây là cách duy nhất mô phỏng đúng việc dự đoán tương lai.
- **Giải thích bằng SHAP:** với mỗi người vay, chỉ ra yếu tố nào đẩy rủi ro lên hay kéo xuống.

### Bước 4: So sánh với LendingClub

- **Độ phân biệt (AUC):** máy của bạn và hạng của LendingClub, bên nào tách người trả nợ và người vỡ nợ tốt hơn.
- **Độ chính xác của xác suất:** khi máy nói "10% rủi ro", có đúng khoảng 10% số người đó vỡ nợ không.
- **Bảng theo nhóm:** chia người vay thành 10 nhóm theo điểm của máy, so tỷ lệ vỡ nợ thực tế với hạng LendingClub đã cho.
- **Tìm chỗ lệch:** những người LendingClub xếp hạng tốt nhưng máy của bạn thấy rủi ro, và ngược lại.

### Bước 5: Tính toán tài chính

- **Lợi nhuận thực tế mỗi khoản vay:** (tổng tiền đã thu về − số tiền cho vay) / số tiền cho vay.
- **Tỷ lệ mất khi vỡ nợ:** với các khoản vỡ nợ, phần tiền gốc không thu hồi được.
- **Tổn thất kỳ vọng:** khả năng vỡ nợ × tỷ lệ mất khi vỡ nợ × số tiền vay.
- **Lãi suất "công bằng":** mức lãi vừa đủ bù tổn thất kỳ vọng cộng một mức lời hợp lý. So với lãi thật để tìm nhóm bị tính quá cao hoặc quá thấp.

### Bước 6: Mô phỏng đầu tư

So sánh 4 chiến lược trên dữ liệu kiểm tra: (1) cho mọi khoản vay; (2) chỉ hạng A và B; (3) chọn khoản lãi cao nhất; (4) trong mỗi hạng, chọn 20% khoản an toàn nhất theo máy của bạn. Với mỗi chiến lược, tính lợi nhuận trung bình, tỷ lệ vỡ nợ và mức dao động.

### Bước 7: Phân tích nhóm bị từ chối

- So sánh các thông tin mà cả hai bảng đều có: số tiền xin vay, tỷ lệ nợ trên thu nhập, điểm rủi ro, thâm niên làm việc, bang.
- Tìm "ngưỡng" mà LendingClub có vẻ dùng để từ chối.
- **Cẩn thận:** cần kiểm tra định nghĩa từng cột có thay đổi theo thời gian không, và chỉ kết luận về sự khác biệt, không kết luận về nguyên nhân.

## Kế hoạch 14 tuần

Mỗi tuần khoảng 2–4 giờ, gồm buổi làm việc với mentor và thời gian tự làm. Cột "Nộp" là sản phẩm bạn gửi mentor cuối tuần để kiểm tra.

| Tuần | Học gì | Làm gì | Nộp |
| --- | --- | --- | --- |
| 1 | VS Code, Python cơ bản, Git | Cài đặt môi trường, tạo kho GitHub, viết chương trình Python đầu tiên | Kho GitHub có file README đầu tiên |
| 2 | pandas: đọc, lọc, lưu dữ liệu | Tải dữ liệu từ Kaggle, chọn cột, lọc khoản vay đã kết thúc, lưu Parquet | File dữ liệu sạch + bảng giải thích cột |
| 3 | Vẽ biểu đồ với Plotly; thống kê mô tả | Tỷ lệ vỡ nợ theo hạng, năm, mục đích vay, thu nhập | Notebook với 6–8 biểu đồ có nhận xét |
| 4 | Lãi suất, rủi ro, lợi nhuận | Tính lợi nhuận thực tế theo hạng; viết 2–3 giả thuyết | Bảng lợi nhuận theo hạng + giả thuyết |
| 5 | Học máy là gì; hồi quy logistic | Tạo thông tin đầu vào, chia dữ liệu theo thời gian, xây mô hình 1 | Mô hình logistic + độ chính xác ban đầu |
| 6 | LightGBM; cách tránh "học thuộc" dữ liệu | Xây mô hình 2, so sánh với mô hình 1 | Bảng so sánh 2 mô hình |
| 7 | AUC, đường hiệu chuẩn, SHAP | So máy của bạn với hạng A–G; giải thích dự đoán | Bảng so sánh với LendingClub + biểu đồ SHAP |
| 8 | Tổn thất kỳ vọng, lãi suất công bằng | Tính lãi công bằng theo nhóm, tìm nhóm bị tính sai | Bảng lãi thật vs lãi công bằng |
| 9 | Đầu tư và danh mục | Mô phỏng 4 chiến lược; phân tích nhóm bị từ chối | Kết quả mô phỏng + 3–5 phát hiện chính |
| 10 | Streamlit cơ bản | Dựng khung app, trang "Định giá khoản vay" | App chạy trên máy với trang đầu tiên |
| 11 | Biểu đồ tương tác trong app | Trang "Thử làm nhà đầu tư" và "Máy của tôi vs. LendingClub" | App 3 trang |
| 12 | Kiểm thử, triển khai | Trang "Ai bị từ chối?", viết test, đưa app lên Streamlit Cloud | Link app công khai |
| 13 | Viết báo cáo khoa học | Viết báo cáo tiếng Anh, có mục "những lỗi tôi đã gặp" | Bản nháp báo cáo |
| 14 | Trình bày dự án | Hoàn thiện README, sửa báo cáo, quay video demo 2 phút | Bộ hồ sơ dự án hoàn chỉnh |

Với 2–4 giờ mỗi tuần, các tuần 6, 9 và 12 thường nặng nhất. Nếu cần, có thể giãn lộ trình thành 16 tuần.

## Công cụ bạn sẽ học dùng

Tất cả đều miễn phí và là công cụ mà các nhà phân tích dữ liệu, kỹ sư fintech đang dùng hằng ngày.

| Công cụ | Dùng để làm gì |
| --- | --- |
| VS Code | Phần mềm viết code chính của dự án |
| Python | Ngôn ngữ lập trình phổ biến nhất trong phân tích dữ liệu |
| pandas | Đọc, lọc, tính toán trên bảng dữ liệu hàng triệu dòng |
| Plotly | Vẽ biểu đồ đẹp, có thể bấm và phóng to |
| scikit-learn, LightGBM | Xây "máy chấm điểm" người vay |
| SHAP | Giải thích vì sao máy chấm một người là rủi ro |
| Streamlit | Biến code Python thành trang web tương tác |
| Git, GitHub | Lưu lại mọi thay đổi và công khai dự án cho hội đồng xem |

Sau dự án, bạn có thể ghi những kỹ năng này vào CV một cách trung thực, vì bạn đã thật sự dùng chúng để làm ra một sản phẩm.

## Cấu trúc kho code

Toàn bộ dự án nằm trong một thư mục, mở bằng VS Code. Cách sắp xếp này giống các dự án chuyên nghiệp, giúp người xem hiểu ngay mỗi phần làm gì.

```
lendingclub-fair-rates/
├── src/lc_rates/          # Code chính, chia theo việc
│   ├── config.py          #   Đường dẫn, danh sách cột, năm chia dữ liệu
│   ├── data.py            #   Đọc và làm sạch dữ liệu
│   ├── features.py        #   Tạo thông tin đầu vào
│   ├── model.py           #   Huấn luyện và đánh giá mô hình
│   └── finance.py         #   Lợi nhuận, tổn thất kỳ vọng, lãi công bằng, mô phỏng đầu tư
├── scripts/               # Chạy từng bước từ đầu đến cuối
│   ├── download_data.py
│   ├── train.py
│   ├── analyze.py
│   └── build_app_data.py
├── app/                   # Trang web Streamlit
│   ├── streamlit_app.py
│   └── pages/             #   4 trang của app
├── notebooks/             # Phân tích khám phá, viết như bài hướng dẫn
├── models/                # Mô hình đã huấn luyện
├── results/               # Bảng và biểu đồ kết quả
├── report/                # Báo cáo nghiên cứu
├── tests/                 # Kiểm tra tự động
├── README.md              # Trang giới thiệu dự án
├── requirements.txt       # Danh sách thư viện cần cài
└── .gitignore             # Loại dữ liệu gốc và khóa Kaggle khỏi GitHub
```

Dữ liệu gốc (khoảng 1,6 GB) và khóa Kaggle không bao giờ được đưa lên GitHub. Chỉ phần dữ liệu đã thu gọn cho app mới được lưu trong kho.

## Tiêu chí hoàn thành

Dự án được coi là hoàn thành khi đạt đủ các tiêu chí dưới đây. Bạn có thể tick dần trong quá trình làm.

**Dữ liệu và phân tích**

- [ ] Chỉ dùng khoản vay đã kết thúc và đã đủ thời gian đáo hạn
- [ ] Không có cột "nhìn trước tương lai" nào trong đầu vào của mô hình
- [ ] Mỗi biểu đồ có tiêu đề, đơn vị và một câu nhận xét

**Mô hình**

- [ ] Dữ liệu được chia theo thời gian (năm cũ để học, năm mới để kiểm tra)
- [ ] Có bảng so sánh rõ ràng giữa máy của bạn và hạng A–G của LendingClub
- [ ] Giải thích được ít nhất 5 yếu tố ảnh hưởng mạnh nhất đến rủi ro

**App**

- [ ] Đủ 4 trang, mở bằng link công khai
- [ ] Người không biết code dùng được mà không cần hướng dẫn
- [ ] Có kiểm tra tự động, app chạy không lỗi

**Báo cáo và trình bày**

- [ ] Báo cáo tiếng Anh có đủ: câu hỏi, dữ liệu, cách làm, phát hiện, hạn chế
- [ ] Có mục "những lỗi tôi đã gặp và cách sửa"
- [ ] Mỗi phát hiện chính có một con số cụ thể
- [ ] README trên GitHub có hướng dẫn chạy, link app, link báo cáo
- [ ] Video demo 2 phút

## Bạn nhận được gì, và dùng cho hồ sơ thế nào

**Sau 14 tuần, bạn có:**

- Một app chạy thật trên mạng, có link gửi kèm hồ sơ.
- Một báo cáo nghiên cứu với câu hỏi, cách làm, phát hiện và biểu đồ.
- Một kho code trên GitHub gọn gàng, có hướng dẫn chạy.
- Một video demo 2 phút.

**Phù hợp apply ngành:** Tài chính, Kinh tế, Quản trị kinh doanh, Kế toán, Thống kê, Toán ứng dụng, Data Science. Với ngành Khoa học máy tính, dự án vẫn rất mạnh nhờ phần mô hình và app.

**Đưa vào hồ sơ du học:**

| Phần hồ sơ | Cách dùng dự án |
| --- | --- |
| Hoạt động ngoại khóa (Activities) | Một dòng nêu câu hỏi và kết quả có con số, ví dụ "Phân tích hơn 2 triệu khoản vay để kiểm tra lãi suất có công bằng không; phát hiện…" |
| Bài luận "Why this major" | Kể lúc bạn phát hiện mình sai (ví dụ cái bẫy khoản vay chưa đáo hạn) và điều đó khiến bạn tò mò về ngành tài chính ra sao |
| Thông tin bổ sung / Portfolio | Gửi link app, báo cáo, video để người đọc tự dùng thử |
| Thư giới thiệu | Mentor viết cụ thể về quá trình bạn tự đặt câu hỏi và kiên trì sửa lỗi |
| Phỏng vấn | Một chủ đề bạn nói được 10 phút, có số liệu và ví dụ từ chính dự án |

Không dự án nào đảm bảo kết quả trúng tuyển. Nhưng một sản phẩm thật, do chính bạn làm và giải thích được, giúp hồ sơ của bạn khác biệt giữa hàng nghìn hồ sơ có điểm số tương tự.

## Câu hỏi thường gặp

**Mình chưa biết lập trình, có làm được không?** Được. Mentor hướng dẫn từ bước cài đặt đầu tiên. Bạn cần sự chăm chỉ và tò mò hơn là kinh nghiệm code.

**Mỗi tuần cần dành bao nhiêu thời gian?** Khoảng 2–4 giờ mỗi tuần, gồm buổi làm việc với mentor và thời gian tự làm. Tuần làm app có thể cần nhiều hơn một chút.

**Máy tính cần mạnh cỡ nào?** Một laptop thông thường có RAM 8 GB trở lên là đủ. File dữ liệu gốc khá lớn (khoảng 1,6 GB), nhưng bạn sẽ học cách lọc bớt để máy chạy nhẹ nhàng.

**Trên mạng đã có nhiều dự án về LendingClub, dự án của mình có bị trùng không?** Phần lớn dự án có sẵn chỉ dừng ở "dự đoán ai vỡ nợ". Dự án của bạn đi xa hơn: so sánh với chính LendingClub, tính xem lãi suất có công bằng không, và nhìn cả những người bị từ chối. Các phát hiện và câu chuyện là của riêng bạn.

**Làm xong rồi có phát triển tiếp được không?** Được. Bạn có thể viết bài nghiên cứu ngắn, thi các cuộc thi dữ liệu, hoặc mở rộng sang dữ liệu cho vay của nước khác.
